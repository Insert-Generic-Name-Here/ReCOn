from watchdog.events import PatternMatchingEventHandler
from colorama import Fore, Style
import pandas as pd
import os, time


class WorkspaceWatchDog(PatternMatchingEventHandler):
    def __init__(self, local, workspace_name, verbose=False, patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):   
        super(WorkspaceWatchDog, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)            
        self.local          = local
        self.workspace_name = workspace_name
        self.verbose        = verbose

        self.journal_path = os.path.join(os.path.join(os.path.expanduser('~'), '.recon', 'logs', f'{self.workspace_name}_journal.csv'))
        self.journal_cols = ['timestamp' ,'event' , 'src', 'dest', 'local']
        if not os.path.exists(self.journal_path):
            self.__journal(mode='h', data=self.journal_cols)
        # else:
            # pd.read_csv(self.journal_path, index_col=[0])
        

    def on_moved(self, event):
        super(WorkspaceWatchDog, self).on_moved(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'@{self.workspace_name} {self.__colorize("Moved", "b")} {what}: {event.src_path} to {event.dest_path}')
    
        rec = [timestamp, 'moved', event.src_path, event.dest_path, self.local]
        self.__journal(mode='a', data=rec)
    

    def on_created(self, event):
        super(WorkspaceWatchDog, self).on_created(event)
        timestamp = int(time.time())
            
        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'@{self.workspace_name} {self.__colorize("Created", "g")} {what}: {event.src_path}')
    
        rec = [timestamp, 'created', event.src_path, '', self.local]
        self.__journal(mode='a', data=rec)                          
        
        
    def on_deleted(self, event):
        super(WorkspaceWatchDog, self).on_deleted(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'@{self.workspace_name} {self.__colorize("Deleted", "r")} {what}: {event.src_path}')
    
        rec = [timestamp, 'deleted', event.src_path, '', self.local]
        self.__journal(mode='a', data=rec)
        

    def on_modified(self, event):
        super(WorkspaceWatchDog, self).on_modified(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'@{self.workspace_name} {self.__colorize("Modified", "y")} {what}: {event.src_path}')
    
        rec = [timestamp, 'modified', event.src_path, '', self.local]
        self.__journal(mode='a', data=rec)


    def __journal(self, mode='a', data=None):                   
        if mode is 'a':
            new_row = pd.DataFrame([data], columns=self.journal_cols)
            with open(self.journal_path, 'a') as f:
                new_row.to_csv(f, header=False)
            # if self.verbose: print(f'@{self.workspace_name} Activity Saved to {self.workspace_name}.csv Journal!')

        if mode is 'h':
            df = pd.DataFrame(columns=data)
            df.to_csv(self.journal_path)
            if self.verbose: print(f'@{self.workspace_name} Created {self.workspace_name}.csv Journal!')
            # return df

    
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