#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# I wrote this file. As long as you retain this notice you can do whatever you
# want with this stuff. If we meet some day, and you think this stuff is worth
# it, you can buy me a bottle of cider in return.
#
#	Constantin S. Pan <kvapen@gmail.com>
#	2016
# -----------------------------------------------------------------------------

import sys
import os

import parser
import profile

def print_header(h):
	print("--- HEADER")
	print("    protocol: {}".format(h['protocol']))
	print("    profile: {}".format(h['profile']))
	if 'crc' in h:
		print("    crc: {}".format(h['crc']))
		

def print_footer(f):
	print("--- FOOTER")
	print("    crc: {}".format(f['crc']))

def print_message(m, showall):
	msgname = profile.msg_name(m['type'])
	print("--- " + msgname)
	for mtype, fnum, ftype, fval in m['fields']:
		if profile.field_known(mtype, fnum) or showall:
			fname = profile.field_name(mtype, fnum)
			print("    {0}({1}): {2}".format(fname, ftype, fval))

import argparse

def main(args):
	with open(args.filename, 'rb') as f:
		parsed = parser.parse(f)

	print_header(parsed['header'])
	for message in parsed['messages']:
		if not message['head']['definition']:
			if profile.msg_known(message['type']) or args.all:
				print_message(message, showall=args.all)
	print_footer(parsed['footer'])

if __name__ == '__main__':
	aparser = argparse.ArgumentParser(description="Parse a .FIT file.")
	aparser.add_argument('filename', type=str, help='the filename of the .FIT file you want to parse')
	aparser.add_argument('--all', action='store_true', help='show all messages and fields, even of unknown type')
	args = aparser.parse_args()
	main(args)
