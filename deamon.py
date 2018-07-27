import psutil
import configparser
from time import sleep
import os, sys
import getpass
import pickle

# Get the top-level logger object
totaltime = 0

with open("config.pkl", "rb") as fp:   # Unpickling
    applist = pickle.load(fp)
callstack = []

def checkApplist(proc,Applist):
    try:
        if proc.exe() in Applist:
            return True
        return False
    except TypeError:
        return False

while 1:

    for proc in psutil.process_iter():
        if proc.pid == os.getpid(): continue
        if proc.username() != getpass.getuser(): continue
        if proc.status() != 'running': continue
        if checkApplist(proc, applist):
            proc.kill()
            callstack.append(proc.name())

    sleep(1.5)
    if (totaltime  % 50) == 0:
        print ('working')
        with open("config.pkl", "rb") as fp:   # Unpickling
            applist = pickle.load(fp)
    totaltime += 1

