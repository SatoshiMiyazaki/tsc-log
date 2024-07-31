# RegisterData.py
# Register TSC Log data on to sqlite3 database
# Satoshi Miyazaki / Subaru Telescope, NAOJ
# June 9, 2024

import subprocess
from subprocess import PIPE

def shell(command, isVerbose=False):
    if isVerbose:
        print(command)
    proc = subprocess.run(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return proc.stdout, proc.stderr

import os
import pandas as pd
import datetime
import sqlite3
import codecs

class RegisterData():
    def __init__(self, startDateTime, durationInDay, dataType, devName, dbName, isVerbose=False):
        self.startDateTime = startDateTime
        self.durationInDay = durationInDay
        self.dataType = dataType
        self.devName = devName
        self.dbName = dbName
        self.tableName = f'{devName.replace("-", "_")}_{dataType}'
        self.isVerbose = isVerbose

        df = pd.read_csv('telDav/dump-tsc-loghsc.csv', low_memory=False)

        data = df.values

        indexName = 1
        indexDataType = 3
        indexDev = 24

        self.names = []
        for d in data:
            if d[indexDev] == devName and d[indexDataType] == self.dataType:
                if d[indexName].find('Actuator') >= 0 and d[indexName].find('Force') >= 0 and d[indexDev].find('PMFXS') < 0:
                    continue   # skip because too many data
                self.names.append(d[indexName])
        print(f'{self.devName} {self.dataType}: {len(self.names)} found')
        self.numberOfNames = len(self.names)
    
    def run(self):
        if self.dataType == 'E':
            _dataType = 'V'
            _dataTypeForSql = 'integer'
        else:
            _dataType = self.dataType
            _dataTypeForSql = 'float'
    
        extractor = "/usr/local/bin/dump-tsc-log -a -z"

        logDay = self.startDateTime  + datetime.timedelta(days=-1)
        inputFilePath = f"/stars/{logDay.year}/TSC{_dataType}-{logDay.year}{logDay.month:02}{logDay.day:02}-17.pkt"

        conn = sqlite3.connect(self.dbName)
        cur = conn.cursor()

        cur.execute(f'SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="{self.tableName }"')
        if cur.fetchone() == (0,): #tableが存在しないとき
            print(f"table {self.tableName} not found. creating ...")
            sqlCommandString = f'create table {self.tableName}("index" integer, "#rxdate" string, "rxtime(HST)" string, "sec-from-00:00:00UTC" float,'
            for name in self.names:
                sqlCommandString += f'\"{name}\" {_dataTypeForSql}, '
            sqlCommandString += f'"datetime" datetime primary key)'
            cur.execute(sqlCommandString)
        else: # tableが存在するとき　
            df = pd.read_sql(f"SELECT max(datetime) FROM {self.tableName}", conn)
            maxDatetime = df['max(datetime)'][0]
            if maxDatetime == None:
                print(f"table {self.tableName} found but no data found")
                return
#            print(maxDatetime)
            print(f"table {self.tableName} found. The last time stamp is {maxDatetime} .")
            inputFilePath = self.nextFilePathFromMaxDatetime(maxDatetime, _dataType)
#            print(inputFilePath)
            

        for i in range(self.durationInDay*2):
            if not os.path.exists(inputFilePath):
                if self.isVerbose:
                    print(f"Inputfile: '{inputFilePath}' not exist")
                inputFilePath = self.nextInputFilePath(inputFilePath)
                continue

            extractNames = f''
            for name in self.names:
                extractNames += f'-e \"{name}\" '

            (_, outputText) = shell(f'{extractor} {extractNames} {inputFilePath}', isVerbose=self.isVerbose)


            outputFilePaths = self.extractOutputFilePaths(outputText.split('\n'))

            if self.isVerbose:
                print(len(outputFilePaths), ' output files found')
                
            if len(outputFilePaths) == 0:
                outputFilePath = ""
            elif len(outputFilePaths) == 1:
                outputFilePath = outputFilePaths[0]
            else: 
                # more than one file are genereted by the extractor merge then into one csv file
                outputFilePath = self.mergeFiles(outputFilePaths)
            
            if not os.path.exists(outputFilePath):
                if self.isVerbose:
                    print(f"Outputfile: '{outputFilePath}' not exist ({inputFilePath}, {self.devName})")
                inputFilePath = self.nextInputFilePath(inputFilePath)
                continue

            if len(outputFilePaths) == 1:
                with codecs.open(outputFilePath, "r", "Shift-JIS", "ignore") as f:
                    df = pd.read_table(f)
            else: # in case of more than log files are genereted they were merged into a csv file
                df = pd.read_csv(outputFilePath)
                df = df.drop(columns=df.columns[0])
                
            df['datetime']= pd.to_datetime(df['#rxdate'] + ' ' + df['rxtime(HST)'])
            inputFileStartDatetime = self.datetimeFromFilePath(inputFilePath)
        
            df = df.drop(index=[0]) # because the first row is a duplication of the last row in the previous data set
            df = df[df['sec-from-00:00:00UTC'] > 0] # because some contamination exist
            df = df[df['datetime'] > inputFileStartDatetime] # because weird contamination exist
        
            df = df.drop_duplicates(subset=['datetime'])
            df.to_sql(f'{self.tableName}', conn, if_exists='append')
        
            os.remove(outputFilePath)
            inputFilePath = self.nextInputFilePath(inputFilePath)

        cur.close()
        conn.close()

    def nextInputFilePath(self, inputFilePath):
        dataType = inputFilePath[15:16]
        year = int(inputFilePath[17:21])
        month = int(inputFilePath[21:23])
        day = int(inputFilePath[23:25])
        hour = int(inputFilePath[26:28])
    
        if hour == 8:
            hour = 17
            return f"/stars/{year}/TSC{dataType}-{year}{month:02d}{day:02d}-{hour:02d}.pkt"
        else:
            hour = 8
            _dateTime = datetime.datetime(year, month, day, hour, 0, 0) + datetime.timedelta(days=1)
            return f"/stars/{_dateTime.year}/TSC{dataType}-{_dateTime.year}{_dateTime.month:02d}{_dateTime.day:02d}-{hour:02d}.pkt"

    def mergeFiles(self, files):
        outputFilePath = ""
        if not os.path.exists(files[0]):
            return ""
            
        with codecs.open(files[0], "r", "Shift-JIS", "ignore") as f:
            df = pd.read_table(file, delimiter=",")
        os.remove(files[0])

        for i in range(len(files)-1):
            if not os.path.exists(files[i+1]):
                continue

            with codecs.open(files[i+1], "r", "Shift-JIS", "ignore") as f:
                df2 = pd.read_table(f)
                df2 = df.drop(['#rxdate', 'rxtime(HST)', 'sec-from-00:00:00UTC'], axis=1)
                df = pd.merge(df, df2)
                
            os.remove(files[i+1])
            
        outputFilePath = f'{files[0]}_merged.csv'
        df.to_csv(outputFilePath) 
        return outputFilePath

    def extractOutputFilePaths(self, lines):
        paths = []
        for line in lines:
            if line.find('creating') >= 0:
                paths.append(line[11:])

        return paths
    
    def datetimeFromFilePath(self, filePath):
        year = int(filePath[17:21])
        month = int(filePath[21:23])
        day = int(filePath[23:25])
        hour = int(filePath[26:28])
        return datetime.datetime(year, month, day, hour, 0, 0)

    def nextFilePathFromMaxDatetime(self, maxDatetime, dataType):
        year = maxDatetime[0:4]
        month = maxDatetime[5:7]
        day = maxDatetime[8:10]
        hour = int(maxDatetime[11:13])
        
#        if (hour < 7) or (hour > 16):  # fixed on July 18
        if (hour < 7) or (hour > 17):
            print(f"warning: lack of data may be found ... skip to 8 {self.tableName}")
            hour = 8
        elif (hour > 7) and (hour < 15):
            print(f"warning lack of data may be found ... skip to 17 {self.tableName}")
            hour = 17
        else:
            hour += 1
        return f"/stars/{year}/TSC{dataType}-{year}{month}{day}-{hour:02d}.pkt"
        
def readTscDataInformation():
    return pd.read_csv('telDav/dump-tsc-loghsc.csv', low_memory=False)

