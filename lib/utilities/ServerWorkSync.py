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
        direxists = self.__directory_exists(os.path.join(self.remotepath, os.path.split(self.localpath)[1]))
        
        if not direxists:
            print ("> Initiating Handshake. Transferring All Data to SSH Server...")
            self.__cwd_scp(self.localpath, self.remotepath)
        else:
            # TODO: Make handhake on existing directory.
            # Steps:
            #       1.   Compare Directories
            #       2.1. Copy new Files
            #       2.2. Replace old Files with newer ones
            pass   
        
        
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