import connections
import subprocess
import configparser
import paramiko
from server_setup import server_ini_creator
import env_config

### INIs

server_ini_creator(path='~/.recon/')

### Trees
def create_tree():
	return 'mkdir ~/.recon && mkdir ~/.recon/envs && mkdir ~/.recon/config'

## Local tree
subprocess.Popen(create_tree().split(), stdout=subprocess.PIPE)

## Server tree
connections.connect_to_server(create_tree)

### LAS

### Conda envs 

selected_env = env_config.select_env()
env_config.upload_env(selected_env)

### configure server

# Send remote py setup script

servers = configparser.ConfigParser()
servers.read('~/.recon/servers.ini')
for host in servers.sections():
	target_file = f'/home/{servers[host]['uname']}/.recon/remote_setup.py'
	s = paramiko.SSHClient()
	s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		s.connect(servers[host]['host'],22,username=servers[host]['uname'],timeout=4)

		sftp = s.open_sftp()
		sftp.put('remote_setup.py', target_file)
		stdin, stdout, stderr = s.exec_command(f'python {target_file} {selected_env}')
		s.close()
	except: 
		print(f"Server {host} is unavailable.")





### SSH configuration



