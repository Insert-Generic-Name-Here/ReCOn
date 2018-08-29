import paramiko
from watchdog.events import PatternMatchingEventHandler
import os
import errno


class ServerWorkSync(PatternMatchingEventHandler):
    def __init__(self, ssh_client, localpath, remotepath, patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):   
        super(ServerWorkSync, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)    
        self.localpath = localpath
        self.root = os.path.split(localpath)[1]
        self.remotepath = remotepath
        self.sftp_client = ssh_client.open_sftp()
        
        self.__handshake()


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
                print (f'Created directory {dir_}')
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
                print (f'\tCopying {os.path.join(walker[0],file)}...')
                self.sftp_client.put(os.path.join(walker[0],file),os.path.join(remotepath,walker[0],file)) 
        os.chdir(tmp)
    
    
    def __handshake(self):
        direxists = self.__directory_exists(os.path.join(self.remotepath, self.root))
        
        if not direxists:
            print ("> Initiating Handshake. Transferring All Data to SSH Server...")
            self.__cwd_scp(self.localpath, self.remotepath)
        else:
            ''' Update the old Files; Delete the files (and Directories) that don't exist on client '''
            for root, _, files in self.__remote_os_walk(os.path.join(self.remotepath, self.root)):
                dir_of_interest = ''.join(root.split(self.root, 1)[1:]).strip('/')
                server_files = [os.path.join(root, file) for file in files]

                for idx, file in enumerate(server_files):
                    try:
                        mtime_server = self.sftp_client.stat(file).st_mtime
                        mtime_local  = os.stat(os.path.join(self.localpath, dir_of_interest, files[idx])).st_mtime
                        if (mtime_local > mtime_server):
                            print(f'Updated file: {file}')
                            self.sftp_client.put(os.path.join(self.localpath, dir_of_interest, files[idx]), file)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            print(f'Deleted file: {file}')
                            self.sftp_client.remove(file)
                            if not os.path.exists(os.path.join(self.localpath, dir_of_interest)) and len(self.sftp_client.listdir(root)) == 0:
                                print(f'Deleted directory: {root}')                                
                                self.sftp_client.rmdir(root)           
            

            ''' Copy the new Files (and Directories) from the Client to the Server Workspace '''
            for root, _, files in os.walk(os.path.abspath(self.localpath)):
                rel_dir_of_file = ''.join(root.split(self.root, 1)[1:]).strip('/')
                dir_of_interest = os.path.join(self.remotepath, self.root, rel_dir_of_file)
                
                try:
                    self.sftp_client.stat(dir_of_interest)
                except IOError as e:
                    if e.errno == errno.ENOENT:
                        print (dir_of_interest)
                        self.mkdir_p(dir_of_interest, is_dir=True)
                        
                for file in files:
                    try:
                        self.sftp_client.stat(os.path.join(self.remotepath, self.root, rel_dir_of_file, file))
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            remote_file_path = os.path.join(self.remotepath, self.root, rel_dir_of_file, file)
                            print(f'Created file: {remote_file_path}')
                            self.sftp_client.put(os.path.join(root, file), remote_file_path, callback=None, confirm=True)

        
    def on_moved(self, event):
        super(ServerWorkSync, self).on_moved(event)

        what = 'directory' if event.is_directory else 'file'
        print(f'Moved {what}: from {event.src_path} to {event.dest_path}')
        
        try:
            self.sftp_client.posix_rename(os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')), 
                                          os.path.join(self.remotepath, self.root, ''.join(event.dest_path.split(self.root, 1)[1:]).strip('/')))
        except FileNotFoundError:
            pass
    
    
    def on_created(self, event):
        super(ServerWorkSync, self).on_created(event)

        what = 'directory' if event.is_directory else 'file'
        print(f'Created {what}: {event.src_path}')
        
        try:
            if event.is_directory:
                self.sftp_client.mkdir(os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')))
            else:
                self.sftp_client.put(event.src_path,
                                     os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')),
                                     callback=None, confirm=True)
        except FileNotFoundError:
            pass

        
    def on_deleted(self, event):
        super(ServerWorkSync, self).on_deleted(event)

        what = 'directory' if event.is_directory else 'file'
        print(f'Deleted {what}: {event.src_path}')
        
        try:
            if event.is_directory:
                self.sftp_client.rmdir(os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')))  
            else:
                self.sftp_client.remove(os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')))  
        except FileNotFoundError:
            pass
        
        
    def on_modified(self, event):
        super(ServerWorkSync, self).on_modified(event)
        
        what = 'directory' if event.is_directory else 'file'
        print(f'Modified {what}: {event.src_path}')
        
        try:
            if event.is_directory:
                # NOTE: idk if this event is useful for directories, so i'll leave it for future use.
                pass
            else:
                self.sftp_client.put(event.src_path,
                                     os.path.join(self.remotepath, self.root, ''.join(event.src_path.split(self.root, 1)[1:]).strip('/')),
                                     callback=None, confirm=True)
        except FileNotFoundError:
            pass