import os,sys

# set to path of virtualenv python binary
INTERP = "/n/fs/dmca/dmca-staging/dmca/dmca-staging/bin/python"
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

os.environ['CS_ENV'] = 'development' # dont forget to set this!

from main import app as application
