from pathlib import Path
import os

def log_out_err(output, errors, server_name, logpath):
    with open(os.path.join(logpath, f"{server_name}-logs.out"), "a") as outfile:
        outfile.write(output.read().decode('utf8'))
    with open(os.path.join(logpath, f"{server_name}-logs.err"), "a") as errfile:
        errfile.write(errors.read().decode('utf8'))

def init_logs(logpath, servers_dict):  
    for srv in servers_dict:
        hostname_prefix = f"{srv}-logs"
        stdout_data_filename = os.path.join(logpath,f"{hostname_prefix}.out")
        stderr_data_filename = os.path.join(logpath,f"{hostname_prefix}.err" )   
        Path(stdout_data_filename).touch()
        Path(stderr_data_filename).touch()

def log_observer(msg, logpath, server_name):
    with open(os.path.abspath(os.path.join(logpath, f'{server_name}-observer.logs')), 'a') as outfile:
        outfile.write(msg)