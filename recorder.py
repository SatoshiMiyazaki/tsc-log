# recorder.py
# Launcher of processes to register TSC Log data on to sqlite3 database
# Satoshi Miyazaki / Subaru Telescope, NAOJ
# June 9, 2024

import datetime
import threading

from telDav import RegisterData

df = RegisterData.readTscDataInformation()
print(df.info())

threads = []
dataTypes = ['E', 'L', 'S']
for dataType in dataTypes:
    for devName in df['DevName'].drop_duplicates():
        if type(devName) != str:
            continue
        if 'PMA' in devName:
            continue

        registerData = RegisterData.RegisterData(startDateTime = datetime.datetime(year=2021, month=1, day=1), 
                                             durationInDay = 365*4, 
                                             dataType = dataType, 
                                             devName = devName, 
                                             dbName = f'db/{devName.replace("-", "_")}_{dataType}.db',
                                             isVerbose = False
                                            )
        if registerData.numberOfNames > 0:
            threads.append(threading.Thread(target=registerData.run))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
    