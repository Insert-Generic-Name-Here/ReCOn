from tqdm import tqdm
import pandas as pd
import threading
import getpass
import psutil
import queue
import time
import os

class CPUMonitor(object):
    def __init__(self, interval=5, logData=False, data_path=None):
        """
        CPU Monitor
        :type interval: int
        :param interval: (default = 5) Check interval, in seconds.
        :type logData: bool
        :param logData: (default = False) if True, logged data will be output to a File; if False , logged data will be output to stdout.
        :type data_path: string
        :param data_path: (default = None) if logData is True data_path must hold the directory in which the daemon will write the data.
        """
        self.interval = interval

        if (not logData):
            self.queue = queue.Queue(maxsize=2)
        else:
            if (data_path is None):
                raise ValueError('data_path must not be None.')
            self.data_path = data_path

        print ('cwd @monitor.cpu module: ', os.getcwd() )
        
        thread = threading.Thread(target=self.run, args=(logData,))
        thread.daemon = True                            # Daemonize thread
        thread.start()   # Start the execution

    def __FetchCPUProcesses(self, mostImportant=10):
        procs = []
        for proc in psutil.process_iter():
            if proc.pid == os.getpid(): continue 
            if getpass.getuser() in proc.username():
                procs.append({'pid':            proc.pid,
                              'cpu_percent':    proc.cpu_percent(),
                              'memory_percent': proc.memory_percent(),
                              'name':           proc.name(),
                              'cmdline':        proc.cmdline(),
                              'status':         proc.status()
                             })
        process_log = pd.DataFrame(procs)
        tmp = process_log.sort_values(['memory_percent'], ascending=False)[:10]
        return tmp


    def run(self, logData=False):
        """ Method that runs forever in the thread """
        while True:
            cpuProcs = self.__FetchCPUProcesses()
            
            if (logData):
                # if file does not exist write header
                if not os.path.isfile(os.path.join(self.data_path, 'cpu_log.csv')):
                    cpuProcs.to_csv(os.path.join(self.data_path, 'cpu_log.csv'), index=False)
                    print("@CPUDaemon -> Writing Records.")
                # else it exists so append without writing the header
                else:
                    cpuProcs.to_csv(os.path.join(self.data_path, 'cpu_log.csv'), mode='a', header=False, index=False)
                    print("@CPUDaemon -> Appending Records.")
            else:
                ''' 
                    TODO: Return the DataFrame to main for Prediction 
                '''
                #### TEST CODE (NIGHTLY BUILD)
                self.queue.put(cpuProcs)
                
            time.sleep(self.interval)


    def Get_CPU_Processes(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

'''
                            CPU Monitor Toy Example
'''
if __name__ == '__main__':
    ''' How many seconds you want to Fetch Data '''
    totalTime = 40
    cpuMonitor = CPUMonitor(interval=5, logData=True, data_path=os.path.join('.', 'data'))

    for i in tqdm(range(totalTime), ascii=True, desc='Monitoring CPU...'):
        time.sleep(1)
    print('Dataset Created! Bye-Bye')
