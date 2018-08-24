import os
import datetime
import lib.monitor.ProcessMonitor as monitor
from time import gmtime, strftime, sleep


procMonitor = monitor.ProcessMonitor(data_path=os.path.join('.', 'data'), logData=True, interval=5)

while (True):
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), end='\r', flush=True)
    sleep(1)