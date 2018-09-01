import os
import paramiko
import configparser
from lib.connections import select_server, get_servers, close_connection
import lib.ServerWorkSync as sync
from watchdog.observers import Observer
from time import gmtime, strftime, sleep


'''
    las sync --all: Implicit Folder Sync (GOTO: workspace.ini > SYNC ALL PATHS)
    las sync --path WORKSPACE_PATH : Explicit Folder Sync

    las <PROCESS>: Sync all paths on workspace.ini and Execute <PROCESS> on Default Server.
    las --server SERVER_NAME --workspace WORKSPACE_NAME <PROCESS>: Sync selected workspace on workspace.ini and Execute <PROCESS> on Selected Server (SERVER_NAME must be on servers.ini).
'''


def start_watchdog(curr_server, localpath, remotepath, hostname='', verbose=False):
    ## Instantiate a ServerWorkSync WatchDog (handler) as well as a Recursive Observer Object for the given handler
    handler = sync.ServerWorkSync(curr_server['connection'], localpath = localpath, hostname=hostname, remotepath = remotepath, verbose=verbose)  
    observer = Observer()
    observer.schedule(handler, path = localpath, recursive = True)
    observer.start()
    return observer


def close_watchdog(server_observers):
    for host, workspace_observers in server_observers.items():
        for workspace_name, observer in workspace_observers.items():
            print (f'\t[+] Closing the {host} Observer for {workspace_name} ...')
            observer.stop()
            observer.join()


def synchronize(workspaces_ini_path, servers_ini_path, host_name='', daemon_mode=True, verbose=False):
    ssh_config = configparser.ConfigParser()
    ssh_config.read(os.path.join(servers_ini_path, 'servers.ini'))
    # ssh_config.read(os.path.join(os.environ['RECON_LOCAL_PATH'],'servers.ini'))

    workspaces = configparser.ConfigParser()
    workspaces.read(workspaces_ini_path)
    
    servers = {}
    server_observers = {}

    if host_name:
        # curr_server = get_servers(os.path.join(os.environ['RECON_LOCAL_PATH'],'servers.ini'), host_name=host_name)
        curr_server = get_servers(os.path.join(servers_ini_path, 'servers.ini'), host_name=host_name)
        servers[host_name] = curr_server
    else:
        for host_name in workspaces.sections():
            # Initiating the Connection
            # curr_server = get_servers(os.path.join(os.environ['RECON_LOCAL_PATH'],'servers.ini'), host_name=host_name)
            curr_server = get_servers(os.path.join(servers_ini_path, 'servers.ini'), host_name=host_name)
            servers[host_name] = curr_server

    for host_name, curr_server in servers.items():
        # Initiating the Client and Server paths
        ## Get The HOME Directory of the SSH Server
        _, stdout, _ = curr_server['connection'].exec_command("echo $HOME")
        ssh_server_home_dir = stdout.readlines()[0].split('\n')[0]
        
        ## Get the Workspace Directory of SSH Client 
        ssh_client_localpath = workspaces[host_name]
        
        for workspace_name in ssh_client_localpath.keys():
            workspace_observers = {workspace_name:start_watchdog(curr_server, ssh_client_localpath[workspace_name], ssh_server_home_dir, hostname=host_name, verbose=verbose)}
            server_observers.update({host_name:workspace_observers})

    if (not daemon_mode):
        print ('[+] Closing the Observers ...')
        close_watchdog(server_observers)
        print ('[+] All Observers Terminated Successfully.')

        print ('[+] Closing the SSH Connections ...')
        for host_name in servers:
            close_connection(servers, host_name)
        print ('[+] All SSH Connections Terminated Successfully.')
    else:
        try:
            while True:
                print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), end='\r', flush=True)
                sleep(1)
        except KeyboardInterrupt:
            print ('[+] Closing the Observers ...')
            close_watchdog(server_observers)
            print ('[+] All Observers Terminated Successfully.')
        finally:
            print ('[+] Closing the SSH Connections ...')
            for host_name in servers:
                close_connection(servers, host_name)
            print ('[+] All SSH Connections Terminated Successfully.')


# if __name__ == '__main__':
#     sync_workspace('workspaces.ini', 'servers.ini', host_name='')