import os
import sys 
import readline
import glob

def pathCompleter(self,text,state):
    line = readline.get_line_buffer().split()
    
    if '~' in text:
        text = os.path.expanduser('~')        
    # autocomplete directories with having a trailing slash
    if os.path.isdir(text):
        text += '/'

    return [x for x in glob.glob(text+'*')][state]