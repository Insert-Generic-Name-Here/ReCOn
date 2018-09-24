'''
Version 2.0 - Now \w Journals
'''
from watchdog.events import PatternMatchingEventHandler
from colorama import Fore, Style
from lib.rfilecmp import cmp
import stat,csv,time
import pandas as pd
import paramiko
import os,errno


# TODO #1: What to do when the Connection is dropped?
# TODO #2: Algorithm to attempt reconnection 
'''(Hint: Check threading -> Attempt to connect (required data on ssh_client_dict) every X seconds)'''
# TODO #3: Implement a startup script to invoke ServerWorkSync for each workspace @workspaces.ini
'''(Hint: Check the workspace_sync_toy_example.py and generalize its behavior for each workspace'''
# TODO #4: Implement the back-and-forth sync automatically (without executing two separate scripts)


class ServerWorkSync(PatternMatchingEventHandler):
    def __init__(self, ssh_client_dict, localpath, remotepath, hostname='', autosync=False, verbose=False, shallow_filecmp=True,\
                 patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):   
        super(ServerWorkSync, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)    
        self.localpath = localpath
        self.remotepath = remotepath
        self.hostname = hostname
        self.autosync = autosync
        self.verbose = verbose
        self.shallow_filecmp = shallow_filecmp
        self.root = os.path.split(localpath)[1]

        self.ssh_client_dict = ssh_client_dict
        self.sftp_client = ssh_client_dict['connection'].open_sftp()
        
        self.journal_path = os.path.join('..', 'logs', 'journal.csv')
        if not os.path.exists(self.journal_path):
            self.__journal(mode='h', data=['timestamp' ,'event' , 'src', 'dest'])

        self.__handshake()


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


    def __remote_os_walk(self, root):
        files = []
        dirs = []
        
        for f in self.sftp_client.listdir_attr(root):
            if stat.S_ISDIR(f.st_mode):
                dirs.append(f.filename)
            else:
                files.append(f.filename)
        yield root, dirs, files
        for folder in dirs:
            for x in self.__remote_os_walk(self.__unix_path(root, folder)):
                yield x


    def __unix_path(self, *args):
        """Most handle UNIX pathing, not vice versa, enforce standard"""
        return os.path.join(*args).replace('\\', '/')


    def __directory_exists(self, path):
        'os.path.exists for paramiko SCP object'
        try:
            self.sftp_client.stat(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return False
            raise
        else:
            return True


    def mkdir_p(self, remote_path, is_dir=False):
        """
        Bringing mkdir -p to Paramiko. 
        sftp - is a valid sftp object (that's provided by the class)
        remote_path - path to create on server.  
        is_dir - Flag that indicates whether remote_path is a directory or not. 
        
        If remote_path is a directory then the file part is stripped away and mkdir_p continues as usual.
        """
        dirs_ = []
        if is_dir:
            dir_ = remote_path
        else:
            dir_, _ = os.path.split(remote_path)
        while len(dir_) > 1:
            dirs_.append(dir_)
            dir_, _  = os.path.split(dir_)
        if len(dir_) == 1 and not dir_.startswith("/"): 
            dirs_.append(dir_) # For a remote path like y/x.txt 
        while len(dirs_):
            dir_ = dirs_.pop()
            try:
                self.sftp_client.stat(dir_)
            except:
                if self.verbose: print (f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} directory {dir_}')
                self.sftp_client.mkdir(dir_)


    def __cwd_scp(self, localpath, remotepath):
        #  recursively upload a full directory
        tmp = os.getcwd()
        os.chdir(os.path.split(localpath)[0])

        for walker in os.walk(self.root):
            try:
                self.sftp_client.mkdir(os.path.join(remotepath,walker[0]))
            except:
                pass
            for file in walker[2]:
                if self.verbose: print (f'\t{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Copying", "g")} {os.path.join(walker[0],file)}...')
                self.sftp_client.put(os.path.join(walker[0],file),os.path.join(remotepath,walker[0],file)) 
        os.chdir(tmp)


    def __filter_journals(self):
        with self.sftp_client.open(os.path.join(self.ssh_client_dict['recon_path'], 'logs', 'journal.csv'), 'r') as f:
            remote_journal = pd.read_csv(f, index_col=[0])
            remote_journal.iloc[0:0].to_csv(f)
        local_journal  = pd.read_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', 'journal.csv'), index_col=[0])

        fn = pd.concat([remote_journal,local_journal], ignore_index=True)

        fn['rel'] = fn['src'].apply(lambda path: ''.join(path.split(self.root, 1)[1:]).strip('/'))
        exp = fn.loc[fn.groupby(['rel']).timestamp.idxmax()]

        with self.sftp_client.open(os.path.join(self.ssh_client_dict['recon_path'], 'logs', 'journal.csv'), 'w+') as f:
            remote_journal.iloc[0:0].to_csv(f)

        local_journal.iloc[0:0].to_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', 'journal.csv'))
        return exp.drop(['rel'], axis=1)


    def __journal(self, mode='r', data=None):
        if mode is 'r':
            journal = self.__filter_journals()
            for row in journal.iterrows():
                yield row[1]
                    
        if mode is 'w':
            with open(self.journal_path, mode=mode) as f:
                writer = csv.writer(f)
                writer.writerows(data)

        if mode is 'h':
            with open(self.journal_path, mode='w') as f:
                writer = csv.writer(f)
                writer.writeheader(data)


    def __handshake(self):
        direxists = self.__directory_exists(os.path.join(self.remotepath, self.root))
        print (f'{"@"+self.hostname+" " if self.hostname else ""}Initiating Handshake. Updating Remote Server Files...\n')
        
        ''' If the Directory does not Exist (First-Time Syncing) Create the whole Directory Tree '''
        if not direxists:
            self.__cwd_scp(self.localpath, self.remotepath)
        else:
            ''' Read the Journal and Update the Necessary Files '''
            for activity in self.__journal():
                # activity : ['timestamp' ,'event' , 'src', 'dest']
                src_path = activity[2]
                if activity[1] == 'moved':
                    dest_path = activity[3]
                    self.sftp_client.posix_rename(os.path.join(self.remotepath, self.root, ''.join(src_path.split(self.root, 1)[1:]).strip('/')), 
                                                  os.path.join(self.remotepath, self.root, ''.join(dest_path.split(self.root, 1)[1:]).strip('/')))
                elif activity[1] == 'created':
                    dest_path = os.path.join(self.remotepath, self.root, ''.join(src_path.split(self.root, 1)[1:]).strip('/'))
                    if os.path.isdir(src_path):
                        self.sftp_client.mkdir(dest_path)
                    else:
                        self.sftp_client.put(src_path, dest_path, callback=None, confirm=True)
                elif activity[1] == 'deleted':
                    dest_path = os.path.join(self.remotepath, self.root, ''.join(src_path.split(self.root, 1)[1:]).strip('/'))
                    if os.path.isdir(src_path):
                        self.sftp_client.rmdir(dest_path)  
                    else:
                        self.sftp_client.remove(dest_path)  
                elif activity[1] == 'modified':
                    dest_path = os.path.join(self.remotepath, self.root, ''.join(src_path.split(self.root, 1)[1:]).strip('/'))
                    if os.path.isdir(src_path):
                        pass
                    else:
                        if not cmp(src_path, dest_path, self.sftp_client, shallow=self.shallow_filecmp):
                            self.sftp_client.put(src_path, dest_path, callback=None, confirm=True)
            
    
    def on_moved(self, event):
        super(ServerWorkSync, self).on_moved(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Moved", "b")} {what}: from {event.src_path} to {event.dest_path}')
        
        try:
            if self.autosync:
                self.sftp_client.posix_rename(os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')), 
                                            os.path.join(self.remotepath, self.root, ''.join(event.dest_path.split(self.root, 1)[1:]).strip('/')))
            else:
                rec = [timestamp, 'moved', event.src_path, event.dest_path]
                self.__journal(mode='w', data=rec)

        except FileNotFoundError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} does not Exist!')
        except IOError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is Already Moved!')
        
    
    def on_created(self, event):
        super(ServerWorkSync, self).on_created(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} {what}: {event.src_path}')
        
        try:
            if self.autosync:
                dest_path = os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/'))
                if event.is_directory:
                    self.sftp_client.mkdir(dest_path)
                else:
                    self.sftp_client.put(event.src_path, dest_path, callback=None, confirm=True)
            else:
                rec = [timestamp, 'created', event.src_path, '']
                self.__journal(mode='w', data=rec)

        except FileNotFoundError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} does not Exist!')
        except IOError:
            if (event.is_directory):
                if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is Already Created!')
                            
        
    def on_deleted(self, event):
        super(ServerWorkSync, self).on_deleted(event)
        timestamp = int(time.time())

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Deleted", "r")} {what}: {event.src_path}')
        
        try:
            if self.autosync:
                dest_path = os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/'))
                if event.is_directory:
                    self.sftp_client.rmdir(dest_path)  
                else:
                    self.sftp_client.remove(dest_path)  
            else:
                rec = [timestamp, 'deleted', event.src_path, '']
                self.__journal(mode='w', data=rec)

        except FileNotFoundError:
            pass
        except IOError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is Already Deleted!')

        
    def on_modified(self, event):
        super(ServerWorkSync, self).on_modified(event)
        timestamp = int(time.time())
        
        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Modified", "y")} {what}: {event.src_path}')

        try:
            if self.autosync:
                dest_path = os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/'))
                if event.is_directory:
                    # NOTE: idk if this event is useful for directories, so i'll leave it for future use.
                    pass
                else:
                    if not cmp(event.src_path, dest_path, self.sftp_client, shallow=self.shallow_filecmp):
                        self.sftp_client.put(event.src_path, dest_path, callback=None, confirm=True)
                    else:
                        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is the Same (No need for Upload)!')
            else:
                rec = [timestamp, 'modified', event.src_path, '']
                self.__journal(mode='w', data=rec)

        except FileNotFoundError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} does not Exist!')