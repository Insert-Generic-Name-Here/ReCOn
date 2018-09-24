import glob
import stat
import errno
import os, re
import readline
import paramiko
import configparser



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

        # TODO: autocomplete directories with having a trailing slash
        try:
            fileattr = self.sftp_client.lstat(text)
            if stat.S_ISDIR(fileattr.st_mode): text += '/'
        except Exception:
            pass

        cmd = f'import glob; print([x for x in glob.glob(\'{text}\'+\'*\')])'
        _, stdout, _ = self.ssh_client.exec_command(f'{self.remote_conda_dir}/python -c "{cmd}"')
        output = stdout.readlines()
        return [i.strip('\'') for i in output[0].strip('\n[]').split(', ')][state]



def pathCompleter(text,state):
    line = readline.get_line_buffer().split()
    if '~' in text:
        text = os.path.expanduser('~')
    # autocomplete directories with having a trailing slash
    if os.path.isdir(text):
        text += '/'
    return [x for x in glob.glob(text+'*')][state]




################################ DELETE THIS - FOR TESTING PURPOSES ################################
config = configparser.ConfigParser()
config.read(os.path.join('.', 'servers.ini'))

rsa_key = paramiko.RSAKey.from_private_key_file(config['VIRTUALBOX']['pkey'])
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=config['VIRTUALBOX']['host'], username=config['VIRTUALBOX']['uname'], port=config['VIRTUALBOX']['port'], pkey=rsa_key)

stdin, stdout, stderr = ssh_client.exec_command("echo $HOME")
home_dir = stdout.readlines()[0].split('\n')[0]

stdin, stdout, stderr = ssh_client.exec_command("tac .bashrc | grep anaconda*/bin")
stdout.channel.recv_exit_status()
conda_dir = stdout.readlines()
conda_dir = conda_dir[0].split()[1].split('=')[1].strip('\'').strip('"').split(':')[0]
################################ DELETE THIS - FOR TESTING PURPOSES ################################



readline.set_completer_delims('\t')
readline.parse_and_bind("tab: complete")
readline.set_completer(pathCompleter)
info = str(input('Input LOCAL Path...'))


completer = RemotePathCompleter(ssh_client, home_dir, conda_dir)
readline.set_completer_delims('\t')
readline.parse_and_bind("tab: complete")
readline.set_completer(completer.remotePathCompleter)
info = str(input('Input SERVER Path...'))