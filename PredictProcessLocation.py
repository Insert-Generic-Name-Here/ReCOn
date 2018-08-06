import os
import monitor.cpu as cpuMonitor
import monitor.gpu as gpuMonitor

cpuMonitor = cpuMonitor.CPUMonitor(data_path=os.path.join('.', 'data'), logData=False, interval=5)
gpuMonitor = gpuMonitor.GPUMonitor(data_path=os.path.join('.', 'data'), logData=False, interval=10)


while (True):
    cpuProcs = cpuMonitor.Get_CPU_Processes()
    gpuProcs = gpuMonitor.Get_GPU_Processes()
    
    if (cpuProcs is not None):
        print ('\n\t====================\n\tGETTING CPU DATA\n\t====================\n')
        print (cpuProcs)
    
    if (gpuProcs is not None):
        print ('\n\t====================\n\tGETTING GPU DATA\n\t====================\n')
        print (gpuProcs)
        
    '''
        Here, (having the above results) the Prediction will take place 
        as well as the appropriate Process Migration to the Cloud.
    '''