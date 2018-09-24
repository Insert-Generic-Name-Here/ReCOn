import os
import sys 
import readline
import glob
import stat


def pathCompleter(text,state):
    line = readline.get_line_buffer().split()
    
    if '~' in text:
        text = os.path.expanduser('~')        
    # autocomplete directories with having a trailing slash
    if os.path.isdir(text):
        text += '/'

    return [x for x in glob.glob(text+'*')][state]


class RemotePathCompleter:
    def __init__(self, ssh_client, remote_home_dir, remote_conda_dir):
        self.ssh_client = ssh_client
        self.sftp_client = ssh_client.open_sftp()
        self.remote_home_dir = remote_home_dir
        self.remote_conda_dir = remote_conda_dir


    def remotePathCompleter(self, text, state):
        line = readline.get_line_buffer().split()
        if '~' in text:
            text = self.remote_home_dir

        try:
            fileattr = self.sftp_client.lstat(text)
            if stat.S_ISDIR(fileattr.st_mode): text += '/'
        except Exception:
            pass

        cmd = f'import glob; print([x for x in glob.glob(\'{text}\'+\'*\')])'
        _, stdout, _ = self.ssh_client.exec_command(f'{self.remote_conda_dir}/python -c "{cmd}"')
        output = stdout.readlines()
        return [i.strip('\'') for i in output[0].strip('\n[]').split(', ')][state]