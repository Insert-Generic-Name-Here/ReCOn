'''
VERSION 1.0
'''

from watchdog.events import PatternMatchingEventHandler
from colorama import Fore, Style
from lib.rfilecmp import cmp, cmpolder
import paramiko
import os,errno
# from lib.server_logging import log_observer

'''
timestamp, event, what(*), src_path, dest_path
xxxxxxxxx, M    , F   ,    file1,
xxxxxxxxx, R    , F   ,    file1,    file2
xxxxxxxxx, M    , F   ,    file2,
xxxxxxxxx, R    , F   ,    file2,    file3
xxxxxxxxx, M    , F   ,    file3,
'''

'''
TODO: There is one occation the above will fail. If a user renames a file (or directory), both will coexist. **What will happen on that case?**
SOLUTION: Create the Above Journal.  
'''

class ServerWorkSync(PatternMatchingEventHandler):
    def __init__(self, ssh_client, localpath, remotepath, hostname='', verbose=False, shallow_filecmp=True, 
                 patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):   
        super(ServerWorkSync, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)    
        self.localpath = localpath
        self.remotepath = remotepath
        self.hostname = hostname
        self.verbose = verbose
        self.shallow_filecmp = shallow_filecmp

        self.root = os.path.split(localpath)[1]
        self.sftp_client = ssh_client.open_sftp()
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
        import stat
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
    
    
    def __handshake(self):
        cnt = 0
        direxists = self.__directory_exists(os.path.join(self.remotepath, self.root))
        print (f'{"@"+self.hostname+" " if self.hostname else ""}Initiating Handshake. Transferring All Data to SSH Server...\n')
        
        if not direxists:
            self.__cwd_scp(self.localpath, self.remotepath)
        else:
            ''' Update the old Files; Copy (new) Files From Server to Client '''
            for root, _, files in self.__remote_os_walk(os.path.join(self.remotepath, self.root)):
                dir_of_interest = ''.join(root.split(self.root, 1)[1:]).strip('/')
                server_files = [os.path.join(root, file) for file in files]

                if not os.path.exists(os.path.join(self.localpath, dir_of_interest)):
                    os.makedirs(os.path.join(self.localpath, dir_of_interest))
                    if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} directory: {file}')

                for idx, file in enumerate(server_files):
                    print(f'Synchronized {cnt} Files.', end='\r', flush=True)
                    try:
                        src_path = os.path.join(self.localpath, dir_of_interest, files[idx])
                        if not cmp(src_path, file, self.sftp_client, shallow=self.shallow_filecmp) and cmpolder(src_path, file, self.sftp_client):
                            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Updated", "y")} file: {file}')
                            self.sftp_client.put(os.path.join(self.localpath, dir_of_interest, files[idx]), file)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Downloading", "g")} file: {file}')
                            self.sftp_client.get(file, src_path)
                    cnt += 1
            
        if not direxists:
            self.__cwd_scp(self.localpath, self.remotepath)
        else:
            ''' Update the old Files; Copy (new) Files From Server to Client '''
            for root, _, files in self.__remote_os_walk(os.path.join(self.remotepath, self.root)):
                dir_of_interest = ''.join(root.split(self.root, 1)[1:]).strip('/')
                server_files = [os.path.join(root, file) for file in files]

                if not os.path.exists(os.path.join(self.localpath, dir_of_interest)):
                    os.makedirs(os.path.join(self.localpath, dir_of_interest))
                    if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} directory: {file}')

                for idx, file in enumerate(server_files):
                    print(f'Synchronized {cnt} Files.', end='\r', flush=True)
                    try:
                        src_path = os.path.join(self.localpath, dir_of_interest, files[idx])
                        if not cmp(src_path, file, self.sftp_client, shallow=self.shallow_filecmp) and cmpolder(src_path, file, self.sftp_client):
                            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Updated", "y")} file: {file}')
                            self.sftp_client.put(os.path.join(self.localpath, dir_of_interest, files[idx]), file)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Downloading", "g")} file: {file}')
                            self.sftp_client.get(file, src_path)
                    cnt += 1
            
   

            ''' Copy the new Files (and Directories) from Client to the Server '''
            for root, _, files in os.walk(os.path.abspath(self.localpath)):
                rel_dir_of_file = ''.join(root.split(self.root, 1)[1:]).strip('/')
                dir_of_interest = os.path.join(self.remotepath, self.root, rel_dir_of_file)
                
                try:
                    self.sftp_client.stat(dir_of_interest)
                except IOError as e:
                    if e.errno == errno.ENOENT: 
                        self.mkdir_p(dir_of_interest, is_dir=True)
                        
                for file in files:
                    print(f'Synchronized {cnt} Files.', end='\r', flush=True)
                    try:
                        self.sftp_client.stat(os.path.join(self.remotepath, self.root, rel_dir_of_file, file))
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            remote_file_path = os.path.join(self.remotepath, self.root, rel_dir_of_file, file)
                            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} file: {remote_file_path}')
                            self.sftp_client.put(os.path.join(root, file), remote_file_path, callback=None, confirm=True)
                    cnt += 1

        
    def on_moved(self, event):
        super(ServerWorkSync, self).on_moved(event)

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Moved", "b")} {what}: from {event.src_path} to {event.dest_path}')
        
        try:
            self.sftp_client.posix_rename(os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')), 
                                          os.path.join(self.remotepath, self.root, ''.join(event.dest_path.split(self.root, 1)[1:]).strip('/')))
        except FileNotFoundError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} does not Exist!')
        except IOError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is Already Moved!')
    
    
    def on_created(self, event):
        super(ServerWorkSync, self).on_created(event)

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Created", "g")} {what}: {event.src_path}')
        
        dest_path = os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/'))

        try:
            if event.is_directory:
                self.sftp_client.mkdir(dest_path)
            else:
                self.sftp_client.put(event.src_path, dest_path, callback=None, confirm=True)
        except FileNotFoundError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} does not Exist!')
        except IOError:
            if (event.is_directory):
                if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is Already Created!')
                            
        
    def on_deleted(self, event):
        super(ServerWorkSync, self).on_deleted(event)

        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Deleted", "r")} {what}: {event.src_path}')
        
        dest_path = os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/'))

        try:
            if event.is_directory:
                self.sftp_client.rmdir(dest_path)  
            else:
                self.sftp_client.remove(dest_path)  
        except FileNotFoundError:
            pass
        except IOError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is Already Deleted!')

        
    def on_modified(self, event):
        super(ServerWorkSync, self).on_modified(event)
        
        what = 'directory' if event.is_directory else 'file'
        if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{self.__colorize("Modified", "y")} {what}: {event.src_path}')
        
        dest_path = os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/'))

        try:
            if event.is_directory:
                # NOTE: idk if this event is useful for directories, so i'll leave it for future use.
                pass
            else:
                if not cmp(event.src_path, dest_path, self.sftp_client, shallow=self.shallow_filecmp):
                    self.sftp_client.put(event.src_path, dest_path, callback=None, confirm=True)
                else:
                    if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} is the Same (No need for Upload)!')
        except FileNotFoundError:
            if self.verbose: print(f'{"@"+self.hostname+" " if self.hostname else ""}{what}: {event.src_path} does not Exist!')