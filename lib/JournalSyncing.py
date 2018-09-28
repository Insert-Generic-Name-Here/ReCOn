from lib.rfilecmp import cmp
from colorama import Fore, Style
import stat,csv,time
import pandas as pd
import threading
import paramiko
import os,errno


'''(Hint: Check threading -> Attempt to connect (required data on ssh_client_dict) every X seconds)'''
# TODO #3: Implement a startup script to invoke JournalSyncing for each workspace @workspaces.ini
'''(Hint: Check the workspace_sync_toy_example.py and generalize its behavior for each workspace'''
# TODO #4: Implement the back-and-forth sync automatically (without executing two separate scripts)


class JournalSyncing:
    def __init__(self, journal, ssh_client_dict, localpath, remotepath, verbose=False, shallow_filecmp=True):   
        self.ssh_client_dict = ssh_client_dict
        self.localpath       = localpath
        self.remotepath      = remotepath
        self.verbose         = verbose
        self.shallow_filecmp = shallow_filecmp

        self.root            = os.path.split(self.localpath)[1]
        self.sftp_client     = self.ssh_client_dict['connection'].open_sftp()
         
        try:
            with self.sftp_client.open(os.path.join(self.ssh_client_dict['recon_path'], 'logs', 'journal.csv'), 'r') as f:
                self.remote_journal = pd.read_csv(f, index_col=[0])
        except FileNotFoundError:
            self.remote_journal = None
        finally:
            self.local_journal  = journal


    def journal_syncing(self):
        self.__exec_journals()
        self.__clear_journals()
        

    def __exec_journals(self):
        direxists = self.__directory_exists(os.path.join(self.remotepath, self.root))
        print (f'{"@"+self.ssh_client_dict["host"]+" " if self.ssh_client_dict["host"] else ""}Reading the Journals. Updating Remote Server Files...\n')
        
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


    def __filter_journals(self):
        concatenated_journals = pd.concat([self.remote_journal, self.local_journal], ignore_index=True)
        concatenated_journals['rel'] = concatenated_journals['src'].apply(lambda path: ''.join(path.split(self.root, 1)[1:]).strip('/'))
        filtered_journal = concatenated_journals.loc[concatenated_journals.groupby(['rel']).timestamp.idxmax()]
        return filtered_journal.drop(['rel'], axis=1)


    def __clear_journals(self):
        if self.remote_journal is not None:
            with self.sftp_client.open(os.path.join(self.ssh_client_dict['recon_path'], 'logs', 'journal.csv'), 'w+') as f:
                self.remote_journal.iloc[0:0].to_csv(f)

        local_journal  = pd.read_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', 'journal.csv'), index_col=[0])
        local_journal.iloc[0:0].to_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', 'journal.csv'))


    def __journal(self):
        journal = self.__filter_journals()
        for row in journal.iterrows():
            yield row[1] 


    #####################################################################################
    ################################ AUXILIARY FUNCTIONS ################################
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
                if self.verbose: print (f'{"@"+self.ssh_client_dict["host"]+" " if self.ssh_client_dict["host"] else ""}{self.__colorize("Created", "g")} directory {dir_}')
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
                if self.verbose: print (f'\t{"@"+self.ssh_client_dict["host"]+" " if self.ssh_client_dict["host"] else ""}{self.__colorize("Copying", "g")} {os.path.join(walker[0],file)}...')
                self.sftp_client.put(os.path.join(walker[0],file),os.path.join(remotepath,walker[0],file)) 
        os.chdir(tmp)
