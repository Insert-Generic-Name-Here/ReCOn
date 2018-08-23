import subprocess
import bash_commands

def monitor_chromium():    
    process = subprocess.Popen(bash_commands.open_chromium_X('192.168.1.9').split(), stdout=subprocess.PIPE)
    output, error = process.communicate()