import subprocess
import configparser
import paramiko
from lib.server_setup import server_ini_creator, create_dir_tree, get_path
from lib import env_config, connections, workspaces, workspace_sync
import os, time
from pathlib import Path
import pprint
import platform
from distutils.dir_util import copy_tree
from shutil import copy
import json

pp = pprint.PrettyPrinter(indent=4)

#### IF YOU RUN ON MAC , ADD BASHRC TO .profile ###
if platform.system() == 'Darwin':
	subprocess.Popen("echo 'source ~/.bashrc' >> ~/.profile && . ~/.profile",shell=True, stdout=subprocess.PIPE)


#### TREES AND LOGGING ####
## GET THE LOCAL /.RECON PATH AND INITIALIZE LOGS
local_recon_path = get_path()
config_path = os.path.join(local_recon_path,'config')
logpath = os.path.join(local_recon_path, 'logs')

## INITIALIZE THE UNIVERSAL TREE STRUCTURE (FROM LIST DIRS)
print (f'[+] Local Path: {local_recon_path}')
dirs = ['envs', 'config', 'lib', 'logs']

## CREATE LOCAL DIRECTORY TREE AND APPEND IT TO PATH
subprocess.Popen(create_dir_tree(local_recon_path, dirs).split(), stdout=subprocess.PIPE)
subprocess.Popen(f"echo 'export PATH={local_recon_path}:$PATH' >> ~/.bashrc && . ~/.bashrc",shell=True, stdout=subprocess.PIPE)
print ('[+] Created Local Tree.')

## Transfer scripts and lib to recon path ##
copy_tree("lib",f"{local_recon_path}/lib")
copy("las",f"{local_recon_path}")
copy("flas",f"{local_recon_path}")

print ('[+] Local file transfering complete.')

## CREATE THE INI FILE THAT CONTAINS INFO ABOUT THE SERVERS
server_ini_creator(local_recon_path)
print ('[+] Created Configuration ini')
ini_path = os.path.join(config_path, 'servers.ini')

## GET SERVER OBJECTS (N)
servers = connections.get_servers(ini_path)
pp.pprint(servers)

## CREATE REMOTE DIRECTORY TREE (N)
for srv in servers:
	stdin, stdout, stderr = servers[srv]['connection'].exec_command(create_dir_tree(servers[srv]['recon_path'],dirs))
print ('[+] Created Remote Tree.')

#### WORKSPACES ####
# Create workspaces ini
workspace_path = workspaces.workspace_ini_creator(config_path)
workspace_sync.synchronize(workspace_path, os.path.join(local_recon_path,config_path), daemon_mode=False)
print ('[+] Created workspaces ini.')

### ENVIRONMENTS ####
## SELECT THE CONDA ENV THAT WILL BE REPLICATED ON THE SERVERS 
selected_env = env_config.select_env()
print (f'[+] Environment Selected: {selected_env}')

## EXPORT THE SELECTED ENVIRONMENT AS A YML FILE
proc = subprocess.Popen(env_config.export_env(selected_env, local_recon_path), shell=True, stdout=subprocess.PIPE)
proc.wait()
print (f'[+] Saved {selected_env} yml File.')

## UPLOAD SELECTED ENVIRONMENT ON EACH SERVER (N)
local_env_file_path = f'{local_recon_path}/envs/{selected_env}_envfile.yml'
for srv in servers:
	target_file = f"{servers[srv]['recon_path']}/envs/{selected_env}_envfile.yml"
	connections.sftp_upload(local_env_file_path, target_file, servers[srv])

### CREATE ENV AND SET AS DEFAULT ON REMOTE
for srv in servers:
	stdin, stdout, stderr = servers[srv]['connection'].exec_command("tac .bashrc | grep anaconda*/bin")
	stdout.channel.recv_exit_status()
	conda_dir = stdout.readlines()
	print(f'\nConda Directory for {srv} is: {conda_dir}\n')
	try:
		conda_dir = conda_dir[0].split()[1].split('=')[1].strip('\'').strip('"').split(':')[0]
		while 1:
			stdin, stdout, stderr = servers[srv]['connection'].exec_command(env_config.create_env(conda_dir, servers[srv]['uname'], selected_env))
			
			print(f'\n[+] Creating Remote Environment: {selected_env} ...')

			for line in iter(stdout.readline, ""):
				print(line, end="")
			if not stderr.readlines() :
				stdout.channel.recv_exit_status()
				break
			else:
				print('\n[-] Found Incompatible Packages... Fixing')
				error = json.loads(''.join(stderr.readlines()))
				env_config.purge_deps(local_env_file_path,error['bad_deps'])
				target_file = f"{servers[srv]['recon_path']}/envs/{selected_env}_envfile.yml"
				connections.sftp_upload(local_env_file_path, target_file, servers[srv])
				print('\n[+] Fix Complete')



		stdin, stdout, stderr = servers[srv]['connection'].exec_command(env_config.set_default_env(selected_env))

		print(f'[+] Created Remote Environment: {selected_env}')		
		print('[+] Selected Environment is the Default.')
	except IndexError:
		print ('[-] Anaconda unavailable')

connections.close_connection(servers)
print('[+] Setup Complete. Please Open a new Terminal.')