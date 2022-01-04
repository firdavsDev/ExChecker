'''
This module implements functions to operate with files

Author: Adrián Omar Riao Monsalve
'''

from subprocess import Popen, PIPE, STDOUT
import os, sys

# DEFINE PYTHON USER-DEFINE EXCEPTIONS
class SymbLinkError(Exception):
    """Raised when try to get symbolic link and something is wrong"""
    pass

def read_bytes(path):
	with open(path, "rb") as f:
		content = f.read()
	f.close
	return content


def add_line(file, new_line, pos, replace=False):
	f = open(file, 'r')
	new_file_content = ""
	i=1
	for line in f:
		if (i == pos) & (replace):
			new_file_content += new_line+'\n'
		elif (i == pos) & (not replace):
			new_file_content += new_line+'\n'+line
		else:
			new_file_content += line
		i+=1
	f.close()
	
	f = open(file, 'w')
	f.write(new_file_content)
	f.close()

'''
Return the global variables from javascript

NOTE: In the javascript file we must respect indexing
'''
def read_variables_js(path):
	variables_lines = []
	f = open(path, 'r')
	for line in f:
		if ((('let' in line) | ('var' in line)) &
		  (('	' not in line) | ('    ' not in line))):
			variables_lines.append(line)
		else:
			if variables_lines:
				break
	f.close()
	return variables_lines

'''
Return -1 if no line match
'''
def get_line_number(path, l, partial_match=False):
	f = open(path, 'r')
	i = 1
	found = False
	for line in f:
		if partial_match:
			if (l in line):
				found = True
				break
		else:
			if (l == line):
				found = True
				break
		i += 1
	f.close()
	if found:
		return i
	else:
		return -1

def ls(path='.'):
    list = []
    for file in os.listdir(path):
        list.append(file)
    return list

def file_in_folder(file, folder):
    files = ls(folder)
    if file in files:
        return True
    else:
        return False

def get_ref_symb_link(symbolic_link):
    process = Popen(["readlink", "-f", symbolic_link], stdout=PIPE, text=True)
    process.wait()
    if process.returncode == 0:
        out = process.stdout.read()
        if '\n' in out:
            return out[:-1]
        else:
            return out
    else:
        raise SymbLinkError('ERROR: Can not get reference from symbolic link: ' + symbolic_link)
