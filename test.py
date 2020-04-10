import sys
sys.path.append('./src')

import data

attrs = {
    'x':data.Number(5),
    'y':data.Method(lambda x: data.Number(x.val ** 2))
}
