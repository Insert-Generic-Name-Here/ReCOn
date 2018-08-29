import subprocess
import configparser
import paramiko
from lib.server_setup import server_ini_creator, create_dir_tree, get_path
from lib import env_config, connections, server_logging, workspaces
import os, time
from pathlib import Path
import pprint


pp = pprint.PrettyPrinter(indent=4)

#### TREES AND LOGGING ####

## GET THE LOCAL /.RECON PATH AND INITIALIZE LOGS
local_recon_path = get_path()
logpath = os.path.join(local_recon_path, 'logs')

## EXPORT LOCAL RECON PATH TO SYSTEM VARIABLE (via ~/.bashrc)
export_recon_var = f"echo 'export RECON_LOCAL_PATH={local_recon_path}' >> ~/.bashrc && . ~/.bashrc"
subprocess.Popen(export_recon_var.split(), stdout=subprocess.PIPE)

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
server_logging.init_logs(logpath, servers)

## CREATE REMOTE DIRECTORY TREE (N)
for srv in servers:
	stdin, stdout, stderr = servers[srv]['connection'].exec_command(create_dir_tree(servers[srv]['recon_path'],dirs))
	server_logging.log_out_err(stdout, stderr, logpath, srv)

#### LAS ####

#### WORKSPACES ####
# Create workspaces ini
workspaces.workspace_ini_creator(ini_path)

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
	server_logging.log_out_err(stdout, stderr, logpath, srv)
	conda_dir = stdout.readlines()
	conda_dir = conda_dir[0].split()[1].split('=')[1].strip('\'').strip('"').split(':')[0]
	stdin, stdout, stderr = servers[srv]['connection'].exec_command(env_config.create_env(conda_dir, servers[srv]['uname'], selected_env))
	
	print(f'\n[+] Creating Remote Environment: {selected_env} ...')

	for line in iter(stdout.readline, ""):
		print(line, end="")
	stdout.channel.recv_exit_status()
	server_logging.log_out_err(stdout, stderr, logpath, srv)

	stdin, stdout, stderr = servers[srv]['connection'].exec_command(env_config.set_default_env(selected_env))
	server_logging.log_out_err(stdout, stderr, logpath, srv)

	print(f'[+] Created Remote Environment: {selected_env}')		
	print('[+] Selected Environment is the Default.')
	
connections.close_all(servers)
print('[+] Setup Complete. Please Open a new Terminal.')