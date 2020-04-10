import sys
sys.path.append('../src')

import data
import errors
import random as r

def random(*args):
    if len(args) < 2:
        errors.error(f'Random needs 2 arguments, but only got {len(args)}')
    a = float(args[0].val)
    b = float(args[1].val)

    if round(a) != a or round(b) != b:
        return data.Number(r.uniform(a, b))
    else:
        return data.Number(r.randint(a, b))

attrs = {
    'random':data.Method(random),
}
