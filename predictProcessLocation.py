import os
import monitor.ProcessMonitor as monitor
from time import gmtime, strftime, sleep 

procMonitor = monitor.ProcessMonitor(data_path=os.path.join('.', 'data'), logData=False, interval=5)

while (True):
    print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), end='\r', flush=True) 
    runningProcs = GetRunningProcesses()
    
    if (runningProcs is not None):
        print ('\n\t====================\n\tGETTING PROCESS MONITOR DATA\n\t====================\n')
        print (cpuProcs)
    
    '''
        Here, (having the above results) the Prediction will take place 
        as well as the appropriate Process Migration to the Cloud.
    '''
    sleep(1)