import sys
sys.path.append("../src")

import data as data
import errors as errors
import random as r

def randint(*args):
    """Return random number"""
    if len(args) < 2:
        errors.error(f'Random needs 2 arguments, but only got {len(args)}')
    a = float(args[0].val)
    b = float(args[1].val)

    if round(a) != a or round(b) != b:
        return data.Number(r.uniform(a, b))
    else:
        return data.Number(r.randint(a, b))

def choice(**kwargs):
    if len(kwargs) != 1:
        errors.error(f'Choice needs 1 arguement, but got {len(kwargs)}')

    else:
        return data.Type(r.choice(kwargs))


attrs = {
    'choice': data.Method(choice),
    'randint':data.Method(randint),
}
