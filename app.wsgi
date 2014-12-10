import sys
import os

basedir = os.path.abspath(os.path.dirname(__file__))

activate_this = os.path.join(basedir, 'venv', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))
sys.path.append(basedir)

from manager import app as application
