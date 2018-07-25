import psutil
import configparser
from time import sleep

totaltime = 0
config = configparser.ConfigParser()
config.read('config.ini')   # -> "/path/name/"
applist = config.get('INFO', 'APPLIST')

while 1:
    for proc in psutil.process_iter():
        if proc.name() in applist:
            print (f'Send {proc.name()} to server')
    sleep(1)
    totaltime += 1
    if (totaltime  % 60) == 0:
        print ('Reloaded config')
        config.read('config.ini')   # -> "/path/name/"
        applst = config.get('INFO', 'APPLIST')
