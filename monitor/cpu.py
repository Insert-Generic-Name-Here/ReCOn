from tqdm import tqdm
import pandas as pd
import threading
import getpass
import psutil
import time
import os

class CPUMonitor(object):
    """
    Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=1):
        """
        Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
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

    def __FetchGPUProcesses(self, mostImportant=10):
        # TODO: Fetch top X mostImportant records by **gpu** percent
        pass

    def run(self):
        """ Method that runs forever in the thread """
        while True:
            cpuProcs = self.__FetchCPUProcesses()
#             gpuProcs = self.__FetchGPUProcesses() TODO: Implement GPU Monitor

            # if file does not exist write header
            if not os.path.isfile('cpu_log.csv'):
                cpuProcs.to_csv('cpu_log.csv', index=False)
                print("\nWriting Records.\n")
            # else it exists so append without writing the header
            else:
                cpuProcs.to_csv('cpu_log.csv', mode='a', header=False, index=False)
                print("\nAppending Records.\n")

            time.sleep(self.interval)



'''
                            CPU Monitor Toy Example
'''
if __name__ == '__main__':
    ''' How many seconds you want to Fetch Data '''
    totalTime = 40
    cpuMonitor = CPUMonitor(interval=5)
    for i in tqdm(range(totalTime), ascii=True, desc='Monitoring CPU...'):
        time.sleep(1)
    print('Dataset Created! Bye-Bye')
