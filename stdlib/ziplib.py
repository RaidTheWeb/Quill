
import sys
sys.path.append('../src')

import data
import errors
import zipfile

def unzip(file, password=data.String("")):
  zfile = zipfile.ZipFile(file.val)
  zfile.extractall(pwd=password.val)
  

attrs = {
    'extractall': data.Method(unzip),
}
