import subprocess
import configparser
import paramiko
from lib.server_setup import server_ini_creator, create_dir_tree, get_path
from lib import env_config, connections
import os, time
from pathlib import Path
import pprint
import logging

pp = pprint.PrettyPrinter(indent=4)
#connections.init()
#connections.LOCAL_HOME_FOLDER = Path.home()

## GET THE LOCAL /.RECON PATH 

local_recon_path = get_path()
logpath = os.path.join(local_recon_path, 'logs')

## INITIALIZE THE UNIVERSAL TREE STRUCTURE (FROM LIST DIRS)
print (f'[+] Local Path: {local_recon_path}')
dirs = ['envs', 'config', 'lib', 'logs']

## CREATE LOCAL DIRECTORY TREE
subprocess.Popen(create_dir_tree(local_recon_path, dirs).split(), stdout=subprocess.PIPE)
print ('[+] Created Local Tree.')

## CREATE THE INI FILE THAT CONTAINS INFO ABOUT THE SERVERS
server_ini_creator(local_recon_path)
print ('[+] Created Configuration ini')
ini_path = os.path.join(local_recon_path, 'servers.ini')

## GET SERVER OBJECTS (N)
servers = connections.get_servers(ini_path)
pp.pprint(servers)

## INIT THE LOGGING SEQUENCE (N)
logging.init_logs(logpath, servers)

## CREATE REMOTE DIRECTORY TREE (N)
for srv in servers:
    stdin, stdout, stderr = servers[srv]['connection'].exec_command(create_dir_tree(servers[srv]['recon_path'],dirs))
    logging.log_out_err(stdout, stderr, logpath, srv)

# ## CREATE REMOTE DIRECTORY TREE
# connections.connect_to_server(create_dir_tree,ini_path,cmd_args=(dirs,) )
# print ('[+] Created Remote Tree.\n')

### LAS


### Conda envs 

## SELECT THE CONDA ENV THAT WILL BE REPLICATED ON THE SERVERS 
selected_env = env_config.select_env()
print (f'[+] Environment Selected: {selected_env}')

## EXPORT THE SELECTED ENVIRONMENT AS A YML FILE
proc = subprocess.Popen(env_config.export_env(selected_env), shell=True, stdout=subprocess.PIPE)
proc.wait()
# subprocess.Popen(env_config.export_env(selected_env), shell=True, stdout=subprocess.PIPE, executable='/bin/bash')
# subprocess.Popen(['/bin/bash', '-c', env_config.export_env(selected_env)], stdout=subprocess.PIPE)
print (f'[+] Saved {selected_env} yml File.')

# ## UPLOAD SELECTED ENVIRONMENT ON EACH SERVER
# env_config.upload_env(selected_env, ini_path)

## UPLOAD SELECTED ENVIRONMENT ON EACH SERVER (N)
local_env_file_path = f'{local_recon_path}/envs/{selected_env}_envfile.yml'
for srv in servers:
	target_file = f"{servers[srv]['recon_path']}/envs/{selected_env}_envfile.yml"
	connections.sftp_upload(local_env_file_path, target_file, srv)

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