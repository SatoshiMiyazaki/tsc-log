# ApparatusStatus.py
# based on Sato-san's ana-APPARATUS_STATUS.py
# require STATUS.TABLE.tsv, ID-LOCAL.tsv, ID-LOCAL.tsv, ALARM-CAUTION-FAULT.tsv, and SID-STYPE.tsv
# June 19, 2024

import datetime
import csv

class ApparatusStatus():
    def __init__(self, startDatetime, stopDatetime, keyWords):
        self.startDatetime = startDatetime
        self.stopDatetime = stopDatetime
        self.keyWords = keyWords

        if self.startDatetime.strftime('%p') == 'PM':
            logDay = self.startDatetime  + datetime.timedelta(days=1)
        else:
            # AM
            logDay = self.startDatetime
        self.filePath = f'/tscbin/tsc/{logDay.year}/APPARATUS_STATUS.{logDay.year}{logDay.month:02d}{logDay.day:02d}.LOG'
#        print(self.filePath)

        # Read Status List and append dictionary
        with open('telDav/STATUS.TABLE.tsv', 'r') as f:
            f1dat = csv.reader(f, delimiter = '\t')
            self.snamedict = {}
            for row in f1dat:
            	self.snamedict[row[0]] = row[1]
        
        # Read Status List and append dictionary
        with open('telDav/ID-LOCAL.tsv', 'r') as f:
            f2dat = csv.reader(f, delimiter = '\t')
            self.dnamedict = {}
            for row in f2dat:
            	self.dnamedict[row[0]] = row[1]
        
        # Read Alarm Status ID and append dictionary
        with open('telDav/ALARM-CAUTION-FAULT.tsv', 'r') as f:
            f3dat = csv.reader(f, delimiter = '\t')
            self.alarmdict = {}
            for row in f3dat:
            	self.alarmdict[row[0]] = row[1]
        # Read Alarm Status ID and append dictionary
        with open('telDav/SID-STYPE.tsv', 'r') as f:
            f4dat = csv.reader(f, delimiter = '\t')
            self.stypedict = {}
            for row in f4dat:
            	self.stypedict[row[0]] = row[1]
        
    def run(self):
        with open(self.filePath) as f:
            lines = [s.rstrip() for s in f.readlines()] # chop the last CR

        returnList = []
        for line in lines:
            t = line[0:15]    # UT
            flg = line[32:35] # OCR or RCV
            sid = line[38:45] # Status ID
            sname = line[46:] 
        
            date = datetime.date(int(t[:4]), int(t[4:6]), int(t[6:8]))
            time = datetime.time(int(t[8:10]), int(t[10:12]), int(t[12:14]), int(t[14:])*100000)
            ut  = datetime.datetime.combine(date, time)
            hst = ut - datetime.timedelta(hours=10)
        
            if (hst < self.startDatetime) or (hst > self.stopDatetime):
                continue
                
            strHst = hst.strftime('%Y-%m-%d %H:%M:%S.%f')[:21]
        
            result = self.formatMessage(flg, sid, sname, strHst)
        
            numberOfMatch = 0
            for k in self.keyWords:
                if (k in result) == True:
                    numberOfMatch += 1
            if numberOfMatch == len(self.keyWords):
                returnList.append(result)
        return returnList

    # from Sato-san's ana-APPARATUS_STATUS.py
    def formatMessage(self, flg, sid, sname, strHst):
        d = ' '
        did = sid[:4]	# Device ID
        dname = self.did2dname(did)
        alm = self.isAlarm(sid)
        stype = self.sid2stype(sid)
        result = f'{strHst}{d}{stype}{d}{alm:<6}{d}0x{sid}{d}{dname:<4}{d}{sname:<32}{d}{flg}'
        return result

    # from Sato-san's ana-APPARATUS_STATUS.py
    # define Status ID to Status NAME
    def sid2sname(self, id):
        try:
            ret = self.snamedict[id]
        except:
            ret = "Unknown Status"
        return ret
    
    # define Device ID to Device NAME
    def did2dname(self, id):
        try:
            ret = self.dnamedict[id]
        except:
            ret = "Undefined Device"
        return ret
    
    # define isALARM
    def isAlarm(self, id):
        try:
            ret = self.alarmdict[id]
        except:
            ret = "NORMAL"
        return ret
    
    # define Status ID to Status Type
    def sid2stype(self, id):
        try:
            ret = self.stypedict[id]
        except:
            ret = "??"
        return ret




