import subprocess
import configparser
import paramiko
from lib.server_setup import server_ini_creator, create_dir_tree, get_path
from lib import env_config, connections
import os, time
from pathlib import Path


connections.init()
connections.LOCAL_HOME_FOLDER = Path.home()
connections.LOCAL_RECON_PATH = get_path()

### INIs
print (f'[+] Local Path: {connections.LOCAL_RECON_PATH}')
dirs = ['envs', 'config', 'lib']

## Local tree
subprocess.Popen(create_dir_tree(connections.LOCAL_RECON_PATH, dirs).split(), stdout=subprocess.PIPE)
print ('[+] Created Local Tree.')

server_ini_creator(connections.LOCAL_RECON_PATH)
print ('[+] Created Configuration ini')
ini_path = os.path.join(connections.LOCAL_RECON_PATH, 'servers.ini')

## Server tree
connections.connect_to_server(create_dir_tree,ini_path,cmd_args=(dirs,) )
print ('[+] Created Remote Tree.\n')

### LAS


### Conda envs 
selected_env = env_config.select_env()
print (f'[+] Environment Selected: {selected_env}')

proc = subprocess.Popen(env_config.export_env(selected_env), shell=True, stdout=subprocess.PIPE)
proc.wait()
# subprocess.Popen(env_config.export_env(selected_env), shell=True, stdout=subprocess.PIPE, executable='/bin/bash')
# subprocess.Popen(['/bin/bash', '-c', env_config.export_env(selected_env)], stdout=subprocess.PIPE)
print (f'[+] Saved {selected_env} yml File.')

env_config.upload_env(selected_env, ini_path)

### configure server
# Send remote py setup script
servers = configparser.ConfigParser()
servers.read(ini_path)
for host in servers.sections():
	uname = servers[host]['uname']
	port = servers[host]['port']
	pkey = servers[host]['pkey']

	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh_pkey = paramiko.RSAKey.from_private_key_file(pkey)

	try:
		ssh.connect(servers[host]['host'], port=port, pkey=ssh_pkey, username=uname)

		stdin, stdout, stderr = ssh.exec_command("tac .bashrc | grep anaconda*/bin", get_pty=True)

		stdout.channel.recv_exit_status()
		conda_dir = stdout.readlines()
		conda_dir = conda_dir[0].split()[1].split('=')[1].strip('\'').strip('"').split(':')[0]

		stdin, stdout, stderr = ssh.exec_command(env_config.create_env(conda_dir, uname, selected_env), get_pty=True)
		print(f'\n[+] Creating Remote Environment: {selected_env} ...')
		
		for line in iter(stdout.readline, ""):
			print(line, end="")
		stdout.channel.recv_exit_status()

		stdin, stdout, stderr = ssh.exec_command(env_config.set_default_env(selected_env))

		print(f'[+] Created Remote Environment: {selected_env}')		
		print('[+] Selected Environment is the Default.')
		ssh.close()
	except: 
		print(f"Server {host} is unavailable.")

conda_dir = connections.connect_to_server(cmd = "tac .bashrc | grep anaconda*/bin", config_path = ini_path)
conda_dir = conda_dir[0].split()[1].split('=')[1].strip('\'').strip('"').split(':')[0]
connections.connect_to_server(cmd = env_config.create_env, config_path = ini_path, cmd_args=(conda_dir, uname, selected_env))
output = env_config.create_env(conda_dir, uname, selected_env)
print ('[+] Setup Complete.')