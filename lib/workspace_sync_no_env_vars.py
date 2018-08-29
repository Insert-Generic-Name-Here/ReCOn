import os
import paramiko
import configparser
from lib.connections import select_server, get_servers
import lib.ServerWorkSync as sync
from watchdog.observers import Observer
from time import gmtime, strftime, sleep


'''
    las sync --all: Implicit Folder Sync (GOTO: workspace.ini > SYNC ALL PATHS)
    las sync --path WORKSPACE_PATH : Explicit Folder Sync

    las <PROCESS>: Sync all paths on workspace.ini and Execute <PROCESS> on Default Server.
    las --server SERVER_NAME --workspace WORKSPACE_NAME <PROCESS>: Sync selected workspace on workspace.ini and Execute <PROCESS> on Selected Server (SERVER_NAME must be on servers.ini).
'''

def start_watch_dog(curr_server, localpath, remotepath):
    ## Instantiate a ServerWorkSync WatchDog (handler) as well as a Recursive Observer Object for the given handler
    handler = sync.ServerWorkSync(curr_server['connection'], localpath = localpath, remotepath = remotepath)  
    observer = Observer()
    observer.schedule(handler, path = localpath, recursive = True)
    observer.start()
    return observer

def close_watch_dog(observer):
    observer.join()
    observer.stop()


def sync_workspace(workspaces_ini_path, local_recon_path,host_name=''):
    ssh_config = configparser.ConfigParser()
    ssh_config.read(os.path.join(local_recon_path,'servers.ini'))

    workspaces = configparser.ConfigParser()
    workspaces.read(workspaces_ini_path)

    servers = []
    server_observers = {}

    if host_name:
        curr_server = get_servers(os.path.join(local_recon_path,'servers.ini'), host_name=host_name)
        servers.append((host_name, curr_server))
    else:
        for host_name in workspaces.sections():
            # Initiating the Connection
            curr_server = get_servers(os.path.join(local_recon_path,'servers.ini'), host_name=host_name)
            servers.append((host_name, curr_server))


    for host_name, curr_server in servers:
        # Initiating the Client and Server paths
        ## Get The HOME Directory of the SSH Server
        stdin, stdout, stderr = curr_server['connection'].exec_command("echo $HOME")
        ssh_server_home_dir = stdout.readlines()[0].split('\n')[0]
        
        ## Get the Workspace Directory of SSH Client 
        ssh_client_localpath = workspaces[host_name]
        
        for workspace_name in ssh_client_localpath.keys():
            workspace_observers = {workspace_name:start_watch_dog(curr_server, ssh_client_localpath[workspace_name], ssh_server_home_dir)}
            server_observers.update({host_name:workspace_observers})


    print ('[+] Closing the Observers ...')
    for host, workspace_observers in server_observers.items():
        for workspace_name, observer in workspace_observers.items():
            print (f'\t[+] Closing the {host} Observer for {workspace_name} ...')
    print ('[+] All Observers Terminated Successfully.')


    # print ('[+] Closing the SSH Connections ...')
    # for host_name, server in servers:
    #     server['connection'].close()
    #     print (f'\t[+] Closing the SSH Connection for {host_name}')
    # print ('[+] All SSH Connections Terminated Successfully.')
    

# if __name__ == '__main__':
#     sync_workspace('workspaces.ini', host_name='')