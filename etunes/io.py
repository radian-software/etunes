import os
import shutil
import subprocess
import sys

class StandardIO:
    def __init__(self):
        self.DEVNULL = subprocess.DEVNULL
        self.PIPE = subprocess.PIPE
        self.abspath = os.path.abspath
        self.chdir = os.chdir
        self.dirname = os.path.dirname
        self.exists = os.path.exists
        self.get_terminal_size = shutil.get_terminal_size
        self.getcwd = os.getcwd
        self.isdir = os.path.isdir
        self.isfile = os.path.isfile
        self.islink = os.path.islink
        self.join = os.path.join
        self.makedirs = os.makedirs
        self.mkdir = os.mkdir
        self.open = open
        self.run = subprocess.run
        self.splitext = os.path.splitext
        self.stderr = sys.stderr
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.which = shutil.which
