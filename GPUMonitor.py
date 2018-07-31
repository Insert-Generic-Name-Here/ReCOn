import io
import os
import time
import pandas as pd
import subprocess
import threading
import psutil


class GPUMonitor(object):

    def __init__(self, interval=5):
        """
        Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval

        thread = threading.Thread(target=self.NvidiaDaemon, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()   # Start the execution


    def __GetProcessAttributes(self, pids):
        processAttributes = []
        for pid in pids:
            proc = psutil.Process(pid)
            processAttributes.append({'pid':     pid,
                                    'name':    proc.name(),
                                    'exe':     proc.exe(),                  
                                    'cmdline': proc.cmdline(),
                                    'status':  proc.status()})
        processAttributes = pd.DataFrame(processAttributes)
        return processAttributes


    def __MonitorNvidiaGPU(self):
        'Function that monitors Running Processes on Nvidia GPU'
        '''
            Returns a DataFrame (pid, process_name, cmdline, used_gpu_memory, utilization)
        '''
        getGPUProcesses = 'nvidia-smi pmon -c 1 -s mu'
        
        proc = subprocess.Popen(getGPUProcesses, shell=True, stdout=subprocess.PIPE)
        output = proc.stdout.read().decode('utf-8').split('\n')
        
        # Remove the line describing the units of each feature
        del output[1]
        # convert to csv format...
        output[0] = output[0].replace('# ', '')
        output = [line.strip() for line in output]
        output = [','.join(line.split()) for line in output]
        # ...and drop the command feature (will be added later)...
        output = [','.join(line.split(',')[:8]) for line in output]
        # ...and convert to DataFrame
        procsGPU = pd.read_csv(io.StringIO('\n'.join(output)), header=0)
        procsGPUFeats = self.__GetProcessAttributes(procsGPU.pid.values)
        
        return procsGPU.merge(procsGPUFeats, on='pid', how='inner')


    def NvidiaDaemon(self):
        """ Method that runs forever in the thread """
        while True:
            gpuProcs = self.__MonitorNvidiaGPU()
            # if file does not exist write header
            if not os.path.isfile('nvidia_log.csv'):
                gpuProcs.to_csv('nvidia_log.csv', index=False)
                print("\nWriting Records.\n")
            # else it exists so append without writing the header
            else:
                gpuProcs.to_csv('nvidia_log.csv', mode='a', header=False, index=False)
                print("\nAppending Records.\n")

            time.sleep(self.interval)




'''
                            GPU Monitor Toy Example
'''
if __name__ == '__main__':
    from tqdm import tqdm
    
    ''' How many seconds you want to Fetch Data '''
    totalTime = 20
    gpuMonitor = GPUMonitor(interval=5)

    # i'll run the script for 30 seconds
    for i in tqdm(range(totalTime), ascii=True, desc='Monitoring GPU...'):
        time.sleep(1) 