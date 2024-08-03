# FetchData.py
# Fetch TSC data from SQL Databse
# Satoshi Miyazaki / Subaru Telescope, NAOJ
# June 14, 2024

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import sqlite3

from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import base64

import datetime
import math

class FetchDataTest():
    def __init__(self, startDatetime, stopDatetime, names, dbName="N/A", isVerbose=False, numberOfPlotPoints=0):
        self.startDatetime = startDatetime
        self.stopDatetime = stopDatetime
        self.names = names

        df = pd.read_csv('telDav/dump-tsc-loghsc.csv', low_memory=False)
        for name, i in zip(self.names, range(len(names))):
            dm = df[df['#name(dump-tsc-log)'] == name]
            for d, t in zip(dm['DevName'], dm['ﾃﾞｰﾀ識別']):
                if i == 0:
                    devName = d
                    dataType = t
                    continue
                else:
                    if (d != devName) or (t != dataType):
                        print(f'{name}: DevName ({d}) or DataType ({t}) mismatch with others')
                        print(f'This is a major limitation of the current version of FetchData')
                        print(f'Exiting ...')
                        sys.exit()
        self.dataType = dataType
        self.devName = devName
        if dbName == "N/A":
            self.dbName = f"db/{devName.replace('-', '_')}_{dataType}.db"
        else:
            self.dbName = dbName
        self.isVerbose = isVerbose
        self.numberOfPlotPoints = numberOfPlotPoints

        delta = datetime.datetime.strptime(stopDatetime, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(startDatetime, '%Y-%m-%d %H:%M:%S')

        if self.dataType == 'S':
            self.numberOfData =  delta.total_seconds() * 10
        elif self.dataType == 'L':
            self.numberOfData = delta.total_seconds()
        else: # 'E'
            self.numberOfData = 0  # not used below



    def run(self):
        conn = sqlite3.connect(self.dbName)
        
        items = f'\"#rxdate\", \"rxtime(HST)\"'
        for name in self.names:
            items += f', \"{name}\"'
        
        tableName = f"{self.devName.replace('-', '_')}_{self.dataType}"

        if self.dataType == 'E' or self.numberOfPlotPoints == 0: # no skip
            self.dataframe = pd.read_sql(f"SELECT {items} FROM {tableName} where datetime > '{self.startDatetime}' and datetime < '{self.stopDatetime}'", conn)
        else:
            skip = math.floor(self.numberOfData / self.numberOfPlotPoints)
            self.dataframe = pd.read_sql(f"SELECT {items} FROM {tableName} where datetime > '{self.startDatetime}' and datetime < '{self.stopDatetime}' and rowid % {skip} = 0", conn)
        
        #print(df.info())
        self.dataframe['datetime']= pd.to_datetime(self.dataframe['#rxdate'] + ' ' + self.dataframe['rxtime(HST)'])


    def draw(self, returnPng=False):
        fig, ax = plt.subplots()
        locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        
        for name in self.names:
            ax.plot(self.dataframe['datetime'], self.dataframe[name], label=name)


        plt.legend()
        plt.show()

        if returnPng == True:
            canvas = FigureCanvasAgg(fig)
            s = io.BytesIO()
            canvas.print_png(s)
            return "data:image/png;base64," + base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")

    
        
