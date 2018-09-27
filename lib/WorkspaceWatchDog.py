from watchdog.events import PatternMatchingEventHandler
from colorama import Fore, Style
import pandas as pd
import csv,time
import os


class ServerWorkSync(PatternMatchingEventHandler):
    def __init__(self, verbose=False, autosync=False,\
                 patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):   
        super(ServerWorkSync, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)    

        self.journal_path = os.path.join(os.path.join(os.path.expanduser('~'), '.recon', 'logs', 'journal.csv'))
        if not os.path.exists(self.journal_path):
            self.__journal(mode='h', data=['timestamp' ,'event' , 'src', 'dest'])

        if autosync:
            self.journal = 

    def on_moved(self, event):
        super(ServerWorkSync, self).on_moved(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Moved", "b")} {what}: from {event.src_path} to {event.dest_path}')
    
        rec = [timestamp, 'moved', event.src_path, event.dest_path]
        self.__journal(mode='w', data=rec)
    

    def on_created(self, event):
        super(ServerWorkSync, self).on_created(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} {what}: {event.src_path}')

        rec = [timestamp, 'created', event.src_path, '']
        self.__journal(mode='w', data=rec)                          
        
        
    def on_deleted(self, event):
        super(ServerWorkSync, self).on_deleted(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Deleted", "r")} {what}: {event.src_path}')

        rec = [timestamp, 'deleted', event.src_path, '']
        self.__journal(mode='w', data=rec)
        

    def on_modified(self, event):
        super(ServerWorkSync, self).on_modified(event)
        timestamp = int(time.time())
        
        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Modified", "y")} {what}: {event.src_path}')

        rec = [timestamp, 'modified', event.src_path, '']
        self.__journal(mode='w', data=rec)



    #####################################################################################
    ################################# PRIVATE FUNCTIONS #################################
    #####################################################################################


    def __colorize(self, msg, color):
        ''' (on_moved):     Blue
            (on_created):   Green
            (on_deleted):   Red
            (on_modified):  Yellow '''

        if color is 'b':
            return f'{Style.BRIGHT}{Fore.BLUE}{msg}{Style.RESET_ALL}'
        elif color is 'g':
            return f'{Style.BRIGHT}{Fore.GREEN}{msg}{Style.RESET_ALL}'
        elif color is 'r':
            return f'{Style.BRIGHT}{Fore.RED}{msg}{Style.RESET_ALL}'
        elif color is 'y':
            return f'{Style.BRIGHT}{Fore.YELLOW}{msg}{Style.RESET_ALL}'


    def __journal(self, mode='r', data=None):                   
        if mode is 'w':
            with open(self.journal_path, mode=mode) as f:
                writer = csv.writer(f)
                writer.writerows(data)

        if mode is 'h':
            with open(self.journal_path, mode='w') as f:
                writer = csv.writer(f)
                writer.writeheader(data)