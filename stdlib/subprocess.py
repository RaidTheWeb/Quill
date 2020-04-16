import sys
sys.path.append('../src')

import data
import errors
import subprocess

def call(command):
  subprocess.call(command.val, shell=True)

def getoutput(command):
  return data.String(subprocess.getoutput(command.val))


attrs = {
    'call':            data.Method(call),
    'getoutput':       data.Method(getoutput),
}
