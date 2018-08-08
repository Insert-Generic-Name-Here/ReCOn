import io
import os
import time
import queue
import pandas as pd
import subprocess
import threading
import psutil


class GPUMonitor(object):

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


        print ('cwd @monitor.gpu module: ', os.getcwd() )
        
        if (self.__ExistsNvidia()):
            thread = threading.Thread(target=self.NvidiaDaemon, args=(logData,))
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


    def NvidiaDaemon(self, logData=False):
        """ Method that runs forever in the thread """
        while True:
            gpuProcs = self.__MonitorNvidiaGPU()
            
            if (logData):
                # if file does not exist write header
                if not os.path.isfile(os.path.join(self.data_path, 'nvidia_log.csv')):
                    gpuProcs.to_csv(os.path.join(self.data_path, 'nvidia_log.csv'), index=False)
                    print("@NvidiaDaemon -> Writing Records.")
                # else it exists so append without writing the header
                else:
                    gpuProcs.to_csv(os.path.join(self.data_path, 'nvidia_log.csv'), mode='a', header=False, index=False)
                    print("@NvidiaDaemon -> Appending Records.")
            else:
                ''' 
                    TODO: Return the DataFrame to main for Prediction 
                '''
                #### TEST CODE (NIGHTLY BUILD)
                self.queue.put(gpuProcs)
            
            time.sleep(self.interval)
        

    def Get_GPU_Processes(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

# '''
#                             GPU Monitor Toy Example
# '''
# if __name__ == '__main__':
#     from tqdm import tqdm
    
#     ''' How many seconds you want to Fetch Data '''
#     totalTime = 20
#     gpuMonitor = GPUMonitor(interval=5)

#     # i'll run the script for 30 seconds
#     for i in tqdm(range(totalTime), ascii=True, desc='Monitoring GPU...'):
#         time.sleep(1) 