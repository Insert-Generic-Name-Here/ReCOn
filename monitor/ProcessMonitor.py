import io
import os
import time
import queue
import pandas as pd
import subprocess
import threading
import getpass
import psutil


class ProcessMonitor(object):

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


        print ('cwd @ProcessMonitor module: ', os.getcwd())
        
        nvGpuFlag = self.__ExistsNvidia()
        thread = threading.Thread(target=self.MonitorDaemon, args=(nvGpuFlag,logData,))
        thread.daemon = True
        thread.start()   # Start the execution
        

    def __ExistsNvidia(self):
        getNvidiaDisplay = 'nvidia-smi -L'
        proc = subprocess.Popen(getNvidiaDisplay, shell=True, stdout=subprocess.PIPE)
        output = proc.stdout.read().decode('utf-8').split('\n')
        
        if (output[0] != ''):
            return True
        else:
            return False
        
        
    def __GetProcessAttributes(self, pids):
        processAttributes = []
        for pid in pids:
            proc = psutil.Process(pid)
            processAttributes.append({'pid':     pid,
                                    'cpu_percent': proc.cpu_percent(),
                                    'memory_percent':proc.memory_percent(),
                                    'name':    proc.name(),                
                                    'exe': proc.exe(),
                                    'status':  proc.status()})

        processAttributes = pd.DataFrame(processAttributes)
        return processAttributes


    def __MonitorNvidiaGPU(self):
        '''
            Function that monitors Running Processes on Nvidia GPU
            Returns a DataFrame (pid, process_name, exe, used_gpu_memory, utilization)
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
        # procsGPUFeats = self.__GetProcessAttributes(procsGPU.pid.values)
        # return procsGPU.merge(procsGPUFeats, on='pid', how='inner')
        return procsGPU


    def __MonitorCPU(self, mostImportant=10):
        procs = []
    
        for proc in psutil.process_iter():
            if proc.pid == os.getpid(): continue 
            if proc.status() != 'running': continue 
            try:
                if getpass.getuser() == proc.username():
                    procs.append({'pid':          proc.pid,
                                'cpu_percent':    proc.cpu_percent(),
                                'memory_percent': proc.memory_percent(),
                                'name':           proc.name(),
                                'exe':            proc.exe(),
                                'status':         proc.status()
                                })
            except psutil.AccessDenied:
                continue
                
        process_log = pd.DataFrame(procs, columns=['pid', 'cpu_percent', 'memory_percent', 'name', 'exe', 'status'])
    
        if not process_log.empty:
            return process_log.sort_values(['memory_percent'], ascending=False)[:mostImportant]
        else:
            return process_log


    def __GetCommonRunningProcs(self, cpuProcs, gpuProcs):
        return cpuProcs.merge(gpuProcs, on='pid', how='inner')
         

    def __JoinRunningProcesses(self, cpu_df, gpu_df):
        df = pd.merge(cpu_df, gpu_df, on='pid', how='outer', suffixes=('', '_y'))
        # list comprehension of the cols that end with '_y'
        to_drop = [x for x in df if x.endswith('_y')]
        df.drop(to_drop, axis=1, inplace=True)
        return df


    def MonitorDaemon(self, nvGpuFlag=False, logData=False):
        """
            Method that runs forever in the thread 
        """
        while True:
            cpuProcs = self.__MonitorCPU(mostImportant=10)

            if (nvGpuFlag):
                gpuProcs = self.__MonitorNvidiaGPU()
                runningProcs = self.__GetCommonRunningProcs(cpuProcs, gpuProcs)
            else:
                runningProcs = cpuProcs

            if (logData):
                # if file does not exist write header
                if not os.path.isfile(os.path.join(self.data_path, 'process_log.csv')):
                    runningProcs.to_csv(os.path.join(self.data_path, 'process_log.csv'), index=False)
                    print(f"@MonitorDaemon -> Writing {runningProcs.shape[0]} Records.")
                # else it exists so append without writing the header
                else:
                    runningProcs.to_csv(os.path.join(self.data_path, 'process_log.csv'), mode='a', header=False, index=False)
                    print(f"@MonitorDaemon -> Appending {runningProcs.shape[0]} Records.")
            else:
                # Put Result into Queue
                self.queue.put(runningProcs)

            time.sleep(self.interval)
        

    def GetRunningProcesses(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None