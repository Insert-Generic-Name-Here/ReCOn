import os
import monitor.cpu as cpuMonitor
import monitor.gpu as gpuMonitor

cpuMonitor = cpuMonitor.CPUMonitor(data_path=os.path.join('.', 'data'), logData=True, interval=5)
gpuMonitor = gpuMonitor.GPUMonitor(data_path=os.path.join('.', 'data'), logData=True, interval=10)


while (True):
    continue