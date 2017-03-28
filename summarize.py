#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# I wrote this file. As long as you retain this notice you can do whatever you
# want with this stuff. If we meet some day, and you think this stuff is worth
# it, you can buy me a bottle of cider in return.
#
#	Constantin S. Pan <kvapen@gmail.com>
#	2017
# -----------------------------------------------------------------------------

import sys
import os
import csv

import parser
import profile

def print_message(m, showall):
	msgname = profile.msg_name(m['type'])
	print("--- " + msgname)
	for mtype, fnum, ftype, fval in m['fields']:
		if profile.field_known(mtype, fnum) or showall:
			fname = profile.field_name(mtype, fnum)
			print("    {0}({1}): {2}".format(fname, ftype, fval))

def get_field(m, fieldname, fieldtype):
	for mtype, fnum, ftype, fval in m['fields']:
		if profile.field_known(mtype, fnum):
			fname = profile.field_name(mtype, fnum)
			if fname == fieldname and ftype == fieldtype:
				return fval
	return None

def extract_sessions(filename):
	sessions = []

	with open(filename, 'rb') as f:
		parsed = parser.parse(f)

	for m in parsed['messages']:
		if not m['head']['definition']:
			msgname = profile.msg_name(m['type'])

			if msgname == 'SESSION':
				sport = get_field(m, 'SPORT', 'ENUM')
				subsport = get_field(m, 'SUB_SPORT', 'ENUM')
				if sport == 1 and subsport == 0:
					s = {'sport': 'running'}
				else:
					print("unknown sport {0}:{1}".format(sport, subsport))
					continue

				s['started'  ] =         get_field(m, 'TIMESTAMP', 'UINT32')
				s['steps'    ] =     2 * get_field(m, 'TOTAL_CYCLES', 'UINT32')
				s['kcal'     ] =         get_field(m, 'TOTAL_CALORIES', 'UINT16')
				s['speed.avg'] = 0.001 * get_field(m, 'AVG_SPEED', 'UINT16')
				s['hr.avg'   ] =         get_field(m, 'AVG_HEART_RATE', 'UINT8')
				s['hr.max'   ] =         get_field(m, 'MAX_HEART_RATE', 'UINT8')
				s['cad.avg'  ] =    2 * (get_field(m, 'AVG_CADENCE', 'UINT8')
				                       + get_field(m, 'AVG_FRACTIONAL_CADENCE', 'UINT8') / 256.0)
				s['duration' ] = 0.001 * get_field(m, 'TOTAL_TIMER_TIME', 'UINT32')
				s['distance' ] =  0.01 * get_field(m, 'TOTAL_DISTANCE', 'UINT32')
				sessions.append(s)
			else:
				continue
	return sessions

def getfiles(root):
	paths = []
	for (dirpath, dirnames, filenames) in os.walk(root):
		for filename in filenames:
			if filename.lower().endswith('.fit'):
				paths.append(os.path.join(dirpath, filename))
	return paths

def main(outfilename, *args):
	paths = []
	for name in args:
		if os.path.isdir(name):
			paths.extend(getfiles(name))
		elif os.path.isfile(name):
			paths.append(name)
	sessions = []
	for p in paths:
		new_sessions = extract_sessions(p)
		sessions.extend(new_sessions)

	sessions.sort(key=lambda x: x['started'])
	with open(outfilename, 'w') as csvfile:
		writer = csv.writer(csvfile)

		fields = [
			'started', 'sport', 'steps',
			'kcal', 'speed.avg', 'hr.avg',
			'hr.max', 'cad.avg', 'duration',
			'distance',
		]

		# header
		writer.writerow(fields)

		# data
		for s in sessions:
			writer.writerow(s[f] for f in fields)

if __name__ == '__main__':
	main(*sys.argv[1:])
