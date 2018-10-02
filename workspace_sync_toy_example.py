import os,sys
import signal
import paramiko
import configparser
from functools import partial
from multiprocessing import Process
from watchdog.observers import Observer
from lib.JournalSyncing import JournalSyncing
from lib.WorkspaceWatchDog import WorkspaceWatchDog
from lib.connections import select_server, get_servers
from time import localtime, strftime, sleep, time


def time_cli():
	while True:
		print(strftime("%Y-%m-%d %H:%M:%S", localtime()), end='\r', flush=True)
		sleep(1)


def exit_handler(observers, default_server, clk_thr, signum = None, frame = None):
	if signum: print (f'Signal Handler Called with Signal: {signum}')
	
	print ('\nStopping the Observer...')
	for observer in observers:
		observers[observer].stop()
		
	print ('Closing the SSH Connection...')
	default_server['connection'].close()
	
	clk_thr.join()
	sys.exit(0)


'''
	las sync --all: Implicit Folder Sync (GOTO: workspace.ini > SYNC ALL PATHS)
	las sync --path WORKSPACE_PATH : Explicit Folder Sync

	las <PROCESS>: Sync all paths on workspace.ini and Execute <PROCESS> on Default Server.
	las --server SERVER_NAME --workspace WORKSPACE_NAME <PROCESS>: Sync selected workspace on workspace.ini and Execute <PROCESS> on Selected Server (SERVER_NAME must be on servers.ini).
'''


# TODO: Adjust it for the Generalized <las sync -s "SERVER" -w "WORKSPACE"> Command
if __name__ == '__main__':
	properties = configparser.ConfigParser()
	properties.read(os.path.join('.','config','props.ini'))
	properties = properties['properties']

	workspaces_config = configparser.ConfigParser()
	workspaces_config.read(os.path.join('.','config','workspaces.ini'))

	server_workspaces = workspaces_config[properties['default-server']]
	default_server = get_servers(os.path.join('.','config','servers.ini'), properties['default-server'])
	
	autosync  = True
	handlers  = {}
	observers = {}

	for workspace_name in server_workspaces:
		## Get the Workspace Directory of SSH Client 
		workspace_path = server_workspaces[workspace_name]

		## Instantiate a WorkspaceWatchDog WatchDog (handler)
		handlers[workspace_name] = WorkspaceWatchDog(local=True, verbose=True, workspace_name=workspace_name)
		## Instantiate (and Start) a Recursive Observer Object for the given handler
		observers[workspace_name] = Observer()
		observers[workspace_name].schedule(handlers[workspace_name], path=workspace_path, recursive=True)
		observers[workspace_name].start()




	## Instantiate a JournalSyncing (handler)
	jrnsync = JournalSyncing(default_server, server_workspaces, verbose=True, shallow_filecmp=True)
	
	## Instantiate a CLI Clock for Monitoring the Program's Activity
	clk_thr = Process(target=time_cli)
	clk_thr.start()

	# Handling System Shutdown Gracefully
	## Instantiate a Signal Handler for System Shutdown
	signal.signal(signal.SIGTERM, partial(exit_handler, observers, default_server, clk_thr))
	signal.signal(signal.SIGINT, partial(exit_handler, observers, default_server, clk_thr))


	while True:
		# try:
		jrnsync.journal_syncing()
		sleep(jrnsync.sync_interval)
		# except paramiko.SSHException:
		#     print (f'Can\'t connect to Server {jrnsync.ssh_client_dict["host"]}')
		# except IOError as e:
		#     print(e)
		#     pass
		# except KeyboardInterrupt:
		#     exit_handler(observers, default_server)