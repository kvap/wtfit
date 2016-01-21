import datetime

# -----------------------------------------------------------------------------
# I wrote this file. As long as you retain this notice you can do whatever you
# want with this stuff. If we meet some day, and you think this stuff is worth
# it, you can buy me a bottle of cider in return.
#
#	Constantin S. Pan <kvapen@gmail.com>
#	2016
# -----------------------------------------------------------------------------

def timestamp(ts):
	# Seconds since UTC 00:00 Dec 31 1989
	base = datetime.datetime(1989, 12, 31, 0, 0)
	if ts < 0x10000000:
		# FIXME: system time, need to convert to UTC
		#delta = datetime.timedelta(seconds=ts+0x10000000)
		delta = datetime.timedelta(seconds=ts)
	else:
		delta = datetime.timedelta(seconds=ts)
	return base + delta
