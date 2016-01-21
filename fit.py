#!/usr/bin/python3

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

import profile

def parse_field(f, ftype, fsize, endian):
	if ftype == "ENUM":
		return parse_int(f, 1, fsize, endian, signed=False)
	elif ftype == "SINT8":
		return parse_int(f, 1, fsize, endian, signed=True)
	elif ftype == "UINT8":
		return parse_int(f, 1, fsize, endian, signed=False)
	elif ftype == "SINT16":
		return parse_int(f, 2, fsize, endian, signed=True)
	elif ftype == "UINT16":
		return parse_int(f, 2, fsize, endian, signed=False)
	elif ftype == "SINT32":
		return parse_int(f, 4, fsize, endian, signed=True)
	elif ftype == "UINT32":
		return parse_int(f, 4, fsize, endian, signed=False)
	elif ftype == "STRING":
		return parse_string(f, fsize)
	elif ftype == "FLOAT32":
		return parse_int(f, 4, fsize, endian, signed=False) # FIXME
	elif ftype == "FLOAT64":
		return parse_int(f, 8, fsize, endian, signed=False) # FIXME
	elif ftype == "UINT8Z":
		return parse_int(f, 1, fsize, endian, signed=False)
	elif ftype == "UINT16Z":
		return parse_int(f, 2, fsize, endian, signed=False)
	elif ftype == "UINT32Z":
		return parse_int(f, 4, fsize, endian, signed=False)
	elif ftype == "BYTE":
		return parse_int(f, 1, fsize, endian, signed=False)
	else:
		raise Exception("unknown field type '%s'" % ftype)

def parse_int(f, baselen, length, endian='little', signed=True):
	if baselen == length:
		return int.from_bytes(f.read(length), endian, signed=False)
	else:
		assert(length % baselen == 0)
		r = []
		for i in range(length // baselen):
			r.append(int.from_bytes(f.read(baselen), endian, signed=False))
		return r

def parse_string(f, length):
	return f.read(length).decode('ascii').rstrip('\0')

def parse_header(f):
	r = {}
	r['hlen'] = parse_int(f, 1, 1, signed=False)
	assert(r['hlen'] in (12, 14))
	r['protocol'] = parse_int(f, 1, 1, signed=False)
	r['profile'] = parse_int(f, 2, 2, signed=False)
	r['datalen'] = parse_int(f, 4, 4, signed=False)
	r['fitascii'] = parse_string(f, 4)
	assert(r['fitascii'] == '.FIT')
	if (r['hlen'] == 14):
		r['crc'] = parse_int(f, 2, 2, signed=False)
	return r

def parse_footer(f):
	r = {}
	r['crc'] = parse_int(f, 2, 2, signed=False)
	return r

def parse_file_id(f):
	r = {}
	r['type'] = parse_int(f, 1, 1, signed=False)
	r['manufacturer'] = parse_int(f, 2, 2, signed=False)
	r['product'] = parse_int(f, 2, 2, signed=False)
	r['serial_number'] = parse_int(f, 4, 4, signed=False)
	r['time_created'] = parse_datetime(f)
	r['number'] = parse_int(f, 2, 2, signed=False)
	return r

def parse_fielddef(f):
	r = {}
	r['type'] = parse_int(f, 1, 1, signed=False)
	r['size'] = parse_int(f, 1, 1, signed=False)
	r['basetype'] = profile.base_type_name(parse_int(f, 1, 1, signed=False))
	return r

def parse_messagehead(f):
	r = {}

	header = parse_int(f, 1, 1, signed=False)
	r['compressed']         = bool(header & 0b10000000)
	if r['compressed']:
		r['definition'] = False
		r['localmsgtype']  =      header & 0b01100000
		r['timeoffset'] =      header & 0b00011111
	else:
		r['definition'] = bool(header & 0b01000000)
		r['localmsgtype']  =      header & 0b00001111

	return r

def parse_defmessage(f, head):
	r = {
		'head': head,
	}

	reserved = parse_int(f, 1, 1, signed=False)

	r['endian'] = 'big' if parse_int(f, 1, 1, signed=False) else 'little'

	r['msgtype'] = parse_int(f, 2, 2, r['endian'], signed=False)

	fieldsnum = parse_int(f, 1, 1, signed=False)
	r['fielddefs'] = []
	for i in range(fieldsnum):
		r['fielddefs'].append(parse_fielddef(f))

	return r

def decode_product_name(msg):
	manufacturer = None
	prodname = None

	for f in msg['fields']:
		if profile.field_name(f[0], f[1]) == 'MANUFACTURER':
			manufacturer = f[3]
		if profile.field_name(f[0], f[1]) == 'PRODUCT' and manufacturer is not None:
			f[3] = profile.product_name(manufacturer, f[3])

def decode_fields(msg):
	for f in msg['fields']:
		f[3] = profile.field_decode(f[0], f[1], f[3])

def parse_datamessage(f, head, mdef):
	r = {
		'head': head,
		'type': mdef['msgtype'],
		'fields': [],
	}

	for fdef in mdef['fielddefs']:
		if head['compressed'] and fdef['type'] == 253:
			value = head['timeoffset']
		else:
			value = parse_field(f, fdef['basetype'], fdef['size'], mdef['endian'])

		r['fields'].append([
			mdef['msgtype'],
			fdef['type'],
			fdef['basetype'],
			value,
		])

	decode_product_name(r)
	decode_fields(r)

	return r

message_defs = {}

def parse_message(f):
	head = parse_messagehead(f)
	localmsgtype = head['localmsgtype']
	if head['definition']:
		r = parse_defmessage(f, head)
		message_defs[localmsgtype] = r
	else:
		r = parse_datamessage(f, head, message_defs[localmsgtype])

	return r

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

def main(args):
	f = open(args.filename, 'rb')
	header = parse_header(f)
	print_header(header)

	bytes_read = 0
	while bytes_read < header['datalen']:
		pos = f.tell()
		message = parse_message(f)
		if not message['head']['definition']:
			if profile.msg_known(message['type']) or args.all:
				print_message(message, showall=args.all)
		bytes_read += f.tell() - pos

	footer = parse_footer(f)
	print_footer(footer)

	assert(f.tell() == os.fstat(f.fileno()).st_size)

import argparse

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Parse a .FIT file.")
	parser.add_argument('filename', type=str, help='the filename of the .FIT file you want to parse')
	parser.add_argument('--all', action='store_true', help='show all messages and fields, even of unknown type')
	args = parser.parse_args()
	main(args)
