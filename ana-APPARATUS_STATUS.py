import sys
import csv
import datetime

# define Status ID to Status NAME
def sid2sname(id):
	try:
		ret = snamedict[id]
	except:
		ret = "Unknown Status"
	return ret

# define Device ID to Device NAME
def did2dname(id):
	try:
		ret = dnamedict[id]
	except:
		ret = "Undefined Device"
	return ret

# define isALARM
def isAlarm(id):
	try:
		ret = alarmdict[id]
	except:
		ret = "NORMAL"
	return ret

# define Status ID to Status Type
def sid2stype(id):
	try:
		ret = stypedict[id]
	except:
		ret = "??"
	return ret

argv = sys.argv
argc = len(argv)

if (argc != 2):
	print 'Usage: # python %s [APPARATUS-STATUS-LOG]' % argv[0]
	quit()

# Read Status List and append dictionary
f1 = open('STATUS.TABLE.tsv', 'r')
f1dat = csv.reader(f1, delimiter = '\t')
snamedict = {}
for row in f1dat:
	snamedict[row[0]] = row[1]
f1.close()

# Read Status List and append dictionary
f2 = open('ID-LOCAL.tsv', 'r')
f2dat = csv.reader(f2, delimiter = '\t')
dnamedict = {}
for row in f2dat:
	dnamedict[row[0]] = row[1]
f2.close()

# Read Alarm Status ID and append dictionary
f3 = open('ALARM-CAUTION-FAULT.tsv', 'r')
f3dat = csv.reader(f3, delimiter = '\t')
alarmdict = {}
for row in f3dat:
	alarmdict[row[0]] = row[1]
f3.close()

# Read Alarm Status ID and append dictionary
f4 = open('SID-STYPE.tsv', 'r')
f4dat = csv.reader(f4, delimiter = '\t')
stypedict = {}
for row in f4dat:
	stypedict[row[0]] = row[1]
f4.close()

# main
f = open(argv[1], 'r')
data = csv.reader(f, delimiter = '\t')

## define delimiter for output
#d = '\t'
d = ','

## define header
head = '#NO' + d + 'HST' + d + 'Status Type' + d + 'Alarm/Caution/Fault' + d + d + 'Status ID' + d + 'Device Name' + d + 'Status Name' + d + 'Ocr/Rcv'
print head
count = 0

for pkt in data:
	count += 1
	buf = pkt[0]	# buffer for UT
	date = datetime.date(int(buf[:4]), int(buf[4:6]), int(buf[6:8]))
	time = datetime.time(int(buf[8:10]), int(buf[10:12]), int(buf[12:14]), int(buf[14:])*100000)
	ut  = datetime.datetime.combine(date, time)
	hst = ut - datetime.timedelta(hours=10)
	hst = hst.strftime('%Y-%m-%d %H:%M:%S.%f')
	flg = pkt[1]	# OCR or RCV
	sid = pkt[2]	# Status ID
	did = sid[:4]	# Device ID
	dname = did2dname(did)	# Device Name
	sname = pkt[3]	# Status Name
	alm = isAlarm(sid)
	stype = sid2stype(sid)
	ret = str(count) + d + str(hst)[:21] + d + stype + d + alm + d + d + '0x' + sid + d + dname + d + sname + d + flg
	print ret

f.close()
