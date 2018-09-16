import sys
import subprocess
import configparser
from lib import connections


def create_env(conda_dir, uname, selected_env):
	return f'{conda_dir}/conda env create -n {selected_env} -f /home/{uname}/.recon/envs/{selected_env}_envfile.yml'

def set_default_env(envname):
	return f"echo 'source activate {envname}' >> ~/.bashrc && . ~/.bashrc"

def export_env(selected_env, local_recon_path):
	return f'conda env export --no-builds -n {selected_env} > {local_recon_path}/envs/{selected_env}_envfile.yml'

def yes_no(msg, default_yes=True):
	if default_yes:
		return input(f"{msg} (Y/n) ").lower() != 'n'
	else:
		return input(f"{msg} (y/N) ").lower() == 'y'

def select_env():
	process = subprocess.Popen('which conda'.split(), stdout=subprocess.PIPE)
	conda_dir = process.communicate()[0].decode('utf8').replace('\n', '').split('/bin')[0]
	process = subprocess.Popen(f'ls {conda_dir}/envs'.split(), stdout=subprocess.PIPE)
	envs = process.communicate()[0].decode('utf8').replace('\n', ',')[:-1].split(',') # if empty -> no envs
	
	if envs[0] == '':
		return 'base'
	envs.insert(0, 'base')
	
	while True:
		try: 
			[print (f'[{ind}]{env} ',end='') for ind, env in enumerate(envs)]
			inpt = input ('(Default [0]): ')
			if inpt == '': 
				selected_env = envs[0]
				break
			index_of_env = int(inpt)
			if index_of_env < len(envs):
				selected_env = envs[index_of_env]
				break
			else:
				raise ValueError()
		except ValueError:
			print('Invalid option')
		except KeyboardInterrupt:
			sys.exit()

	return selected_env

def purge_deps(yml_path, bad_deps):
	with open(yml_path, 'r') as f:
		packages = f.readlines()

	for bad_dep in bad_deps:
		for ind, pkg in enumerate(packages):
			if bad_dep in pkg:
				packages.pop(ind)
				print (f'Remove {bad_dep} package from yml')

	with open('py2_test_envfile.yml', 'w') as f:
		f.write(''.join(packages))