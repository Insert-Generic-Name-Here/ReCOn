from watchdog.events import PatternMatchingEventHandler
from colorama import Fore, Style
import pandas as pd
import csv,time
import os


class WorkspaceWatchDog(PatternMatchingEventHandler):
    def __init__(self, local, workspace_name, patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):   
        super(WorkspaceWatchDog, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)    
        
        self.local = local
        self.journal_path = os.path.join(os.path.join(os.path.expanduser('~'), '.recon', 'logs', f'{workspace_name}_journal.csv'))
        if not os.path.exists(self.journal_path):
            self.journal = self.__journal(mode='h', data=['timestamp' ,'event' , 'src', 'dest', 'local'])
        else:
            self.journal = pd.read_csv(self.journal_path, index_col=[0])
        

    def on_moved(self, event):
        super(WorkspaceWatchDog, self).on_moved(event)
        timestamp = int(time.time())

        rec = [timestamp, 'moved', event.src_path, event.dest_path, self.local]
        self.__journal(mode='a', data=rec)
    

    def on_created(self, event):
        super(WorkspaceWatchDog, self).on_created(event)
        timestamp = int(time.time())

        rec = [timestamp, 'created', event.src_path, '', self.local]
        self.__journal(mode='a', data=rec)                          
        
        
    def on_deleted(self, event):
        super(WorkspaceWatchDog, self).on_deleted(event)
        timestamp = int(time.time())

        rec = [timestamp, 'deleted', event.src_path, '', self.local]
        self.__journal(mode='a', data=rec)
        

    def on_modified(self, event):
        super(WorkspaceWatchDog, self).on_modified(event)
        timestamp = int(time.time())
        
        rec = [timestamp, 'modified', event.src_path, '', self.local]
        self.__journal(mode='a', data=rec)


    def __journal(self, mode='a', data=None):                   
        if mode is 'a':
            self.journal.append(pd.DataFrame([rec], cols=self.journal.columns))
            self.journal.to_csv(self.journal_path)

        if mode is 'h':
            df = pd.DataFrame(columns=data)
            df.to_csv(self.journal_path)
            return df