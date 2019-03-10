from lib.rfilecmp import cmp
from colorama import Fore, Style
from time import sleep
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
    def __init__(self, ssh_client_dict, server_workspaces, verbose=False, shallow_filecmp=True, sync_interval=30, reconnect_interval=10):   
        self.ssh_client_dict    = ssh_client_dict
        self.server_workspaces  = server_workspaces
        self.verbose            = verbose
        self.shallow_filecmp    = shallow_filecmp
        self.sync_interval      = sync_interval
        self.reconnect_interval = reconnect_interval
        self.root               = {}           #os.path.split(self.localpath)[1]
        self.sftp_client        = self.ssh_client_dict['connection'].open_sftp()
        self.remote_journals    = {}
        self.remotepath         = ssh_client_dict['connection'].exec_command("echo $HOME")[1].readlines()[0].split('\n')[0]

        for workspace_name in self.server_workspaces:
        ## Get the Workspace Directory of SSH Client 
            workspace_path = self.server_workspaces[workspace_name]

            self.root[workspace_name] = os.path.split(workspace_path)[1]

            direxists = self.__directory_exists(os.path.join(self.remotepath, self.root[workspace_name]))
            if not direxists:
                self.__scp_R(workspace_name)        


    def journal_syncing(self):
        try:
            for workspace_name in self.server_workspaces:
                local_journal = self.__read_local_journal(workspace_name)
                # workspace_path = self.server_workspaces[workspace_name] ## Get the Workspace Directory of SSH Client 
                self.__read_remote_journal(workspace_name)
                self.__exec_journals(local_journal,workspace_name)
                self.__clear_journals(workspace_name)
        except paramiko.SSHException:
            print (f'Can\'t connect to Server {self.ssh_client_dict["host"]}')
            self.__reconnect()


    def __reconnect(self):
        while True:
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_pkey = paramiko.RSAKey.from_private_key_file(self.ssh_client_dict['pkey'])
                ssh_client.connect(hostname=self.ssh_client_dict['host'], username=self.ssh_client_dict['uname'],\
                                port=self.ssh_client_dict['port'], pkey=ssh_pkey)
                
                self.ssh_client_dict['connection'] = ssh_client
                self.sftp_client = self.ssh_client_dict['connection'].open_sftp()
                break
            except paramiko.SSHException:
                print (f'Can\'t connect to Server {self.ssh_client_dict["host"]}')
            except IOError as e:
                print(e)
                pass
            finally:
                sleep(self.reconnect_interval)
        

    def __exec_journals(self, local_journal, workspace_name):
        root = self.root[workspace_name]
        print (f'{root}{"@"+self.ssh_client_dict["host"]} Reading the Journals. Updating Remote Server Files...\n')
        
        ''' If the Directory does not Exist (First-Time Syncing) Create the whole Directory Tree '''
        ''' Read the Journal and Update the Necessary Files '''
        for activity in self.__journal(local_journal, workspace_name):
            # activity : ['timestamp' ,'event' , 'src', 'dest', 'local']
            try:
                src_path = activity[2]
                if activity[1] == 'moved':
                    dest_path = activity[3]
                    
                    if self.verbose: print(f'{workspace_name}@{self.ssh_client_dict["host"]} {self.__colorize("Moved", "b")} {" Directory" if os.path.isdir(src_path) else " File"}:\n[LOCAL PATH] {src_path}\n[SERVER PATH] {dest_path}')

                    self.sftp_client.posix_rename(os.path.join(self.remotepath, root, ''.join(src_path.split(root, 1)[1:]).strip('/')), 
                                                    os.path.join(self.remotepath, root, ''.join(dest_path.split(root, 1)[1:]).strip('/')))
                elif activity[1] == 'created':
                    dest_path = os.path.join(self.remotepath, root, ''.join(src_path.split(root, 1)[1:]).strip('/'))
                    
                    if self.verbose: print(f'{workspace_name}@{self.ssh_client_dict["host"]} {self.__colorize("Created", "g")} {" Directory" if os.path.isdir(src_path) else " File"}:\n[LOCAL PATH] {src_path}\n[SERVER PATH] {dest_path}')
                    
                    if os.path.isdir(src_path):
                        self.sftp_client.mkdir(dest_path)
                    else:
                        self.sftp_client.put(src_path, dest_path, callback=None, confirm=True)
                elif activity[1] == 'deleted':
                    dest_path = os.path.join(self.remotepath, root, ''.join(src_path.split(root, 1)[1:]).strip('/'))
                    
                    if self.verbose: print(f'{workspace_name}@{self.ssh_client_dict["host"]} {self.__colorize("Deleted", "r")} {" Directory" if os.path.isdir(src_path) else " File"}:\n[LOCAL PATH] {src_path}\n[SERVER PATH] {dest_path}')
                    
                    if os.path.isdir(src_path):
                        self.sftp_client.rmdir(dest_path)  
                    else:
                        self.sftp_client.remove(dest_path)  
                elif activity[1] == 'modified':
                    dest_path = os.path.join(self.remotepath, root, ''.join(src_path.split(root, 1)[1:]).strip('/'))
                    
                    if self.verbose: print(f'{workspace_name}@{self.ssh_client_dict["host"]} {self.__colorize("Modified", "y")} {" Directory" if os.path.isdir(src_path) else " File"}:\n[LOCAL PATH] {src_path}\n[SERVER PATH] {dest_path}')
                    
                    if os.path.isdir(src_path):
                        pass
                    else:
                        if not cmp(src_path, dest_path, self.sftp_client, shallow=self.shallow_filecmp):
                            self.sftp_client.put(src_path, dest_path, callback=None, confirm=True)
            except IOError as e:
                if e.errno == errno.ENOENT:
                    print (f'Ommiting {" Directory" if os.path.isdir(src_path) else " File"}: {src_path}')     


    def __read_remote_journal(self,workspace_name):     
        try:
            with self.sftp_client.open(os.path.join(self.ssh_client_dict['recon_path'], 'logs', f'{workspace_name}_journal.csv'), 'r') as f:
                self.remote_journals[workspace_name] = pd.read_csv(f, index_col=[0])
        except FileNotFoundError:
            self.remote_journals[workspace_name] = None


    def __read_local_journal(self,workspace_name):     
        try:
            return pd.read_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', f'{workspace_name}_journal.csv'), index_col=[0])
        except FileNotFoundError:
            return None


    def __filter_journals(self, local_journal, workspace_name):
        concatenated_journals = pd.concat([self.remote_journals[workspace_name], local_journal], ignore_index=True)
        concatenated_journals['rel'] = concatenated_journals['src'].apply(lambda path: ''.join(path.split(self.root[workspace_name], 1)[1:]).strip('/'))
        filtered_journal = concatenated_journals.loc[concatenated_journals.groupby(['rel']).timestamp.idxmax()]
        filtered_journal.drop_duplicates(subset=['timestamp','rel'], keep='last', inplace=True)
        return filtered_journal.drop(['rel'], axis=1)


    def __clear_journals(self, workspace_name):
        if self.remote_journals[workspace_name] is not None:
            with self.sftp_client.open(os.path.join(self.ssh_client_dict['recon_path'], 'logs', f'{workspace_name}_journal.csv'), 'w+') as f:
                self.remote_journals[workspace_name].iloc[0:0].to_csv(f)

        local_journal  = pd.read_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', f'{workspace_name}_journal.csv'), index_col=[0])
        local_journal.iloc[0:0].to_csv(os.path.join(os.path.expanduser('~'), '.recon', 'logs', f'{workspace_name}_journal.csv'))


    def __journal(self, local_journal, workspace_name):
        journal = self.__filter_journals(local_journal, workspace_name)
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


    def __mkdir_p(self, remote_path, is_dir=False):
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
                if self.verbose: print (f'{self.root}{"@"+self.ssh_client_dict["host"]} {self.__colorize("Created", "g")} directory {dir_}')
                self.sftp_client.mkdir(dir_)


    def __scp_R(self, workspace_name):
        #  recursively upload a full directory
        tmp = os.getcwd()

        localpath = self.server_workspaces[workspace_name]
        root  = self.root[workspace_name]

        os.chdir(os.path.split(localpath)[0])
        for walker in os.walk(root):
            try:
                self.sftp_client.mkdir(os.path.join(self.remotepath,walker[0]))
            except:
                pass
            for file in walker[2]:
                if self.verbose: print (f'\t{root}{"@"+self.ssh_client_dict["host"]} {self.__colorize("Copying", "g")} {os.path.join(walker[0],file)}...')
                self.sftp_client.put(os.path.join(walker[0],file),os.path.join(self.remotepath,walker[0],file)) 
        os.chdir(tmp)
