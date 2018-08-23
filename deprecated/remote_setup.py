import os, sys
import subprocess
import sys

def create_env(selected_env):
	return f'conda env create -f ~/.recon/envs/{selected_env}_envfile.yml'

def set_default_env(envname):
	return f"echo 'source activate {envname}' >> ~/.bashrc && . ~/.bashrc"

env = str(sys.argv[1])
process = subprocess.Popen(create_env(env).split(), stdout=subprocess.PIPE)
print(process.communicate())
process = subprocess.Popen(set_default_env(env).split(), stdout=subprocess.PIPE)
print(process.communicate())