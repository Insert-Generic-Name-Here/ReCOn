import os, sys
import subprocess
import bash_commands
import time


def yes_no(msg, default_yes=True):
	if default_yes:
		return input(f"{msg} (Y/n) ").lower() != 'n'
	else:
		return input(f"{msg} (y/N) ").lower() == 'y'


def check_active_env():
	try:  
		return os.environ["CONDA_DEFAULT_ENV"]
	except KeyError:
		return ''

def get_conda_envs():
	process = subprocess.Popen('which conda'.split(), stdout=subprocess.PIPE)
	conda_dir = process.communicate()[0].decode('utf8').replace('\n', '').split('/bin')[0]
	process = subprocess.Popen(f'ls {conda_dir}/envs'.split(), stdout=subprocess.PIPE)
	envs = process.communicate()[0].decode('utf8').replace('\n', ',')[:-1].split(',') # if empty -> no envs
	if envs[0] == '': return ''
	envs.insert(0, 'base')
	return envs

def create_conda_env(name='ReCOn_env'):
	#conda create --name myenv
	subprocess.Popen(f'conda create --{name} myenv'.split(), stdout=subprocess.PIPE)

if __name__ == "__main__":
	envs = get_conda_envs()
	
	if envs == '':
		selected_env = 'base'
	else:
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

	print (selected_env)

	subprocess.Popen(f'conda env export -n {selected_env}> {selected_env}_envfile.yml', stdout=subprocess.PIPE, shell=True)
	p = subprocess.Popen(bash_commands.scp_upload_nokey(f'{selected_env}_envfile.yml', 'theo', '192.168.1.10', port=15123),shell=True)
	out,err = p.communicate()


	

