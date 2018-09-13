import os
import configparser
import readline
from lib.connections import *
from lib.autocompete import *

def workspace_ini_creator(config_path):
    Config = configparser.ConfigParser()
    servers = configparser.ConfigParser()
    servers.read(os.path.join(config_path,'servers.ini'))
    srv = select_server(servers)

    autocomplete_input_path = AutoCompete()
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(autocomplete_input_path.pathCompleter)

    print (f'[+] Configuring workspaces for {srv.name}')
    while(1):
        info = str(input('Add Workspace:Name (Default name -> dir name)\n ex. /home/ReCon : ReCon workspace\n '))

        workspace = [arg.strip() for arg in info.split(':') ]
        if len(workspace)==1:
            w_name = os.path.split(workspace[0])[-1]
            w_path = workspace[0]
        else:
            w_path = workspace[0]
            w_name = workspace[1]
        if os.path.exists(w_path):
            break
        else:
            print('[-] Path not available')


    Config[srv.name] = {w_name: w_path}
    with open(os.path.join(config_path,'workspaces.ini'), 'w+') as configfile:
        Config.write(configfile)
    return os.path.join(config_path,'workspaces.ini')