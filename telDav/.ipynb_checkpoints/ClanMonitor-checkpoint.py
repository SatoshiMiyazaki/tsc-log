# ClanMonitor.py
# based on Sato-san's ana-CLAN_MONITOR.py
# require CMDNAME.LST.tsv, ID-JPDIST.tsv, and CID-DNAME.tsv
# June 19, 2024

import datetime
import csv

class ClanMonitor():
    def __init__(self, startDatetime, stopDatetime, keyWords=[]):
        self.startDatetime = startDatetime
        self.stopDatetime = stopDatetime
        self.keyWords = keyWords

        if self.startDatetime.strftime('%p') == 'PM':
            logDay = self.startDatetime  + datetime.timedelta(days=1)
        else:
            # AM
            logDay = self.startDatetime

        self.filePath = f'/tscbin/tsc/{logDay.year}/CLAN_MONITOR.{logDay.year}{logDay.month:02d}{logDay.day:02d}.LOG'
        print(self.filePath)

        # from Sato-san's ana-CLAN_MONITOR.py
        # read command list
        with open('telDav/CMDNAME.LST.tsv', 'r') as f:
            f1dat = csv.reader(f, delimiter = '\t')
            self.dict1 = {}
            for row in f1dat:
                self.dict1[row[0]] = row[1]
        
        # read command list
        with open('telDav/ID-JPDIST.tsv', 'r') as f:
            f2dat = csv.reader(f, delimiter = '\t')
            self.dict2 = {}
            for row in f2dat:
            	self.dict2[row[0]] = row[1]
        
        # read command list
        with open('telDav/CID-DNAME.tsv', 'r') as f:
            f3dat = csv.reader(f, delimiter = '\t')
            self.dict3 = {}
            for row in f3dat:
            	self.dict3[row[0]] = row[1]
      
    def run(self):
        with open(self.filePath) as f:
            lines = [s.rstrip() for s in f.readlines()] # chop the last CR

        returnList = []
        for line in lines:
            msg = line[24:]
            mst = msg[14:29]
            date = datetime.date(int(mst[:4]), int(mst[4:6]), int(mst[6:8]))
            time = datetime.time(int(mst[8:10]), int(mst[10:12]), int(mst[12:14]), int(mst[14:])*100000)
            ut  = datetime.datetime.combine(date, time)
            hst = ut - datetime.timedelta(hours=10)
            
            if (hst < self.startDatetime) or (hst > self.stopDatetime):
                continue
        
            time = lines[:15]
            mt = msg[0:2]
            dst = msg[2:6]
            src = msg[6:10]
            pid = msg[10:14]
            length = msg[29:33]
            body = msg[33:]
        
            hst = hst.strftime('%Y-%m-%d %H:%M:%S.%f')
            result = self.formatMessage(mt, dst, src, pid, length, body, hst)
            numberOfMatch = 0
            for k in self.keyWords:
                if (k in result) == True:
                    numberOfMatch += 1
            if numberOfMatch == len(self.keyWords):
                returnList.append(result) 
    
        return returnList

    # from Sato-san's ana-CLAN_MONITOR.py
    def cid2cname(self, id):
        try:
            ret = self.dict1[id]
        except:
            ret = "Unknown Command"
        return ret
    
    def cid2jpdsc(sefl, id):
        try:
            ret = self.dict2[id]
        except:
            ret = ""
        return ret
    
    def cid2dname(self, id):
        did = id[:3]
        try:
            ret = self.dict3[did]
        except:
            ret = "Undeined Device"
        return ret
        
    # from Sato-san's ana-CLAN_MONITOR.py
    def formatMessage(self, mt, dst, src, pid, length, body, hst):
    	#ret = mt + d + dst + d + src + d + pid + d + mst + d + length
        d = ' '
        ret = str(hst)[:21] + d + mt + d + src + ' > ' + dst
    #	ret = mt + d + dst + d + src + d + pid + d + str(hst) + d + length
    	# command body analysis
        if mt in {"CC", "CD"}:
            cdn = body[:6]		# command demand number
            cid = body[6:12]	# command id
            prm = body[12:]		# parameter
    		#cnm = dict[cid]		# command name
            cnm = self.cid2cname(cid)		# command name
            dnm = self.cid2dname(cid)
    		#cjp = cid2jpdsc(cid)		# command discription
            ret = ret + d + '0x' + cdn + d + '0x' + cid + d + dnm + d + cnm + d + prm
        elif mt == "CA":
            cdn = body[:6]		# command demand number
            cid = body[6:12]	# command id
            can = body[12:18]	# command acceptance number
            res = body[18:20]	# acceptance result
            inf = body[20:6]	# acceptance infomation
            cnm = self.cid2cname(cid)		# command name
            dnm = self.cid2dname(cid)
            cjp = self.cid2jpdsc(cid)		# command discription
    		#cnm = dict[cid]		# command name
    		#ret = ret + d + '0x' + cdn + d + '0x' + cid + d + cnm + d + '0x' + can + d + res + d + inf
            ret = ret + d + '0x' + cdn + d + '0x' + cid + d + dnm + d + cnm + d + res + d + inf
        elif mt == "CE":
            cdn = body[:6]		# command demand number
            cid = body[6:12]	# command id
            can = body[12:18]	# command acceptance number
            res = body[18:28] 	# execution result
            prm = body[28:]		# executon parameter
            cnm = self.cid2cname(cid)		# command name
            dnm = self.cid2dname(cid)
            cjp = self.cid2jpdsc(cid)		# command discription
    		#ret = ret + d + '0x' + cdn + d + '0x' + cid + d + cnm + d + '0x' + can + d + res + d + prm
            ret = ret + d + '0x' + cdn + d + '0x' + cid + d + dnm + d + cnm + d + res + d + prm
        elif mt == "CR":
            cdn = body[:6]		# command demand number
            cid = body[6:12]	# command id
            gid = body[12:14]	# group id
            mcr = body[14:30]	# macro name 
            exn = body[30:33]	# execution number
            pid = body[33:39]	# primitive command id
            res = body[39:49]	# execution result
            prm = body[49:]		# execution result parameter
            cnm = self.cid2cname(cid)		# command name
            dnm = self.cid2dname(cid)
            cjp = sefl.cid2jpdsc(cid)		# command discription
            ret = ret + d + '0x' + cdn + d + '0x' + cid + d + dnm + d + cnm + d + gid + d + mcr + d + exn + d + pid + d + res + d + prm
        elif mt == "CM":
            cat = body[:1]		# category
            if cat == '1':
                cat = "CAUTION"
            elif cat == '2':
                cat = "ERROR  "
            else:
                cat = "OTHERS "
            mcd = body[1:7]		# message code
            if   mcd == '000001':
                mcd = "OBS-TSC Communication Error"
            elif mcd == '000002':
                mcd = "TWS1-TSC Communication Error"
            elif mcd == '000003':
                mcd = "TWS2-TSC Communication Error"
            elif mcd == '000004':
                mcd = "TWS3-TSC Communication Error"
            elif mcd == '000005':
                mcd = "TSC-MLP1 Communication Error"
            elif mcd == '000006':
                mcd = "TSC-MLP2 Communication Error"
            elif mcd == '000007':
                mcd = "TSC-MLP3 Communication Error"
            else:
                pass 	
            med = body[7:8]		# message enable/disable
            if   med == '0':
                med = "DIS"
            elif med == '1':
                med = "ENA"
            else:
                pass
            msg = body[8:]		# message
            ret = ret + d + d + mcd + d + d + cat + d + msg
        elif mt == "CP":
            cdn = body[:6]		# command demand number
            cid = body[6:12]	# command id
            can = body[12:18]	# command acceptance number
            ukn = body[18:25]	# unknown
            otr = body[25:]		# other
            cnm = self.cid2cname(cid)		# command name
            dnm = self.cid2dname(cid)
            cjp = sefl.cid2jpdsc(cid)		# command discription
    		#ret = ret + d + '0x' + cdn + d + '0x' + cid + d + cnm + d + '0x' + can + d + ukn + d + otr
            ret = ret + d + '0x' + cdn + d + '0x' + cid + d + dnm + d + cnm + d + ukn + d + otr
        else:
            ret = '? ' + ret + d + body
        return(ret)





