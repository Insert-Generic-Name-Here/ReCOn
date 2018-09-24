import os
import readline
import configparser
from pathlib import Path
from lib.autocomplete import *

def get_path():
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(pathCompleter)

    home = str(Path.home())
    def_path = os.path.join(home,'.recon')
    while True:
        path = str(input(f"Select path -> (Default: '{def_path}')\n"))  
        if path == '' : 
            return def_path
        if os.path.exists(path):
            return path
        else:
            print ('invalid')


def create_dir_tree(path,dirs):
    cmd = f"mkdir {path} "
    for folder in dirs:
        cmd += os.path.join(path,str(folder))+ ' '
    return cmd

