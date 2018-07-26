from tqdm import tqdm
import pandas as pd
import threading
import getpass
import psutil
import time
import os

class DataCreator(object):
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
            proc_dct = proc.as_dict()
            if getpass.getuser() in str(proc_dct['username']):
                procs.append({'cpu_percent':proc_dct['cpu_percent'],
                              'memory_percent':proc_dct['memory_percent'],
                              'name':proc_dct['name'],
                              'cmdline':proc_dct['cmdline'],
                              'status':proc_dct['status']
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
            if not os.path.isfile('test_log.csv'):
                cpuProcs.to_csv('test_log.csv', index=False)
                print("\nWriting Records.\n")
            # else it exists so append without writing the header
            else:
                cpuProcs.to_csv('test_log.csv', mode='a', header=False, index=False)
                print("\nAppending Records.\n")

            time.sleep(self.interval)



if __name__ == '__main__':
    ''' How many seconds you want to Fetch Data '''
    totalTime = 40
    dataCrt = DataCreator(interval=0)
    for i in tqdm(range(totalTime)):
        time.sleep(1)
    print('Dataset Created! Bye-Bye')
