# app.py
# Web Interface of TSC Log Display
# Satoshi Miyazaki
# Subaru Telescope / National Astronomical Observaotry of Japan
# June 26, 2024

from flask import Flask, render_template, request
from flask_httpauth import HTTPBasicAuth

import pandas as pd

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import io
import base64

import datetime

from telDav import FetchData
from telDav import ApparatusStatus

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "foo": "foofoo"
}


def draw(df, figsize=(8, 6)):  # not used
	
	fig = Figure(figsize=figsize, facecolor='w', tight_layout=True)
	ax = fig.add_subplot(111)
	
	for col in df.columns:
	    ax.plot(df.index, df[col])
	
	canvas = FigureCanvasAgg(fig)
	s = io.BytesIO()
	canvas.print_png(s)
	
	s = "data:image/png;base64," + base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
	
	return s

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

@app.route('/', methods = ["GET" , "POST"])
@auth.login_required
def index():

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    defaultStartDatetime = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 17, 0, 0).strftime('%Y-%m-%d %H:%M:%S')
    defaultStopDatetime = datetime.datetime(now.year, now.month, now.day, 6, 0, 0).strftime('%Y-%m-%d %H:%M:%S')
    defaultNames = "Weather Temperature, Weather Humidity"
    
    if request.method == 'POST': # POSTの処理
        startDatetime = request.form['startDatetime'] #4 formのname属性を取得
        stopDatetime = request.form['stopDatetime'] #4 formのname属性を取得
        _names = request.form['names'] #4 formのname属性を取得
        names = []
        stringNames = ""
        for name in _names.split(','):
            name = name.strip() 
            names.append(name)
            stringNames += f'{name} '

        print(f"**** \'{startDatetime}\'  \'{stopDatetime}\'")
        fetchData = FetchData.FetchData(startDatetime = startDatetime, 
                                        stopDatetime  = stopDatetime, 
                                        names = names)
        fetchData.run()
    
        return render_template('index.html', 
                               plot=fetchData.draw(returnPng=True),
                               startDatetime=startDatetime,
                               stopDatetime=stopDatetime,
                               names=_names) #5 screen_nameを代入
        
    return render_template('index.html', 
                           startDatetime=defaultStartDatetime,
                           stopDatetime=defaultStopDatetime,
                           names=defaultNames) #6 GETの処理

@app.route('/lastNight', methods = ["GET" , "POST"])
@auth.login_required
def lastNight():
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    defaultReportDate = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 17, 0, 0).strftime('%Y-%m-%d')

    if request.method == 'POST': # POSTの処理
        reportDate = request.form['reportDate']
        startDatetime = reportDate + ' 17:00:00'
        _stopDatetime = datetime.datetime.strptime(startDatetime, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=13)
        stopDatetime = _stopDatetime.strftime('%Y-%m-%d %H:%M:%S')
        
        fetchData = FetchData.FetchData(startDatetime = startDatetime, 
                                        stopDatetime  = stopDatetime, 
                                        names = ['Weather Temperature', 'Weather Humidity'])
        fetchData.run()
        weatherPlot = fetchData.draw(returnPng=True)

        fetchData = FetchData.FetchData(startDatetime = startDatetime, 
                                        stopDatetime  = stopDatetime, 
                                        names = ['AZ Real Angle', 'EL Real Angle'])
        fetchData.run()
        azElPlot = fetchData.draw(returnPng=True)

        apparatusStatus = ApparatusStatus.ApparatusStatus(startDatetime=datetime.datetime.strptime(startDatetime, '%Y-%m-%d %H:%M:%S'),
                                                          stopDatetime=_stopDatetime,
                                                          keyWords=["ALARM"])
        lines = apparatusStatus.run()
        testText = ""
        for l in lines:
            testText += f'{l}\n'
        
        return render_template('lastNight.html', 
                               reportDate=reportDate, 
                               weatherPlot=weatherPlot, 
                               azElPlot=azElPlot,
                               testText=testText)
    
    return render_template('lastNight.html', reportDate=defaultReportDate)
    
if __name__ == "__main__":
    app.run(host='::', port=8001, debug=False)

