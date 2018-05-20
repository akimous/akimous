import this
import numpy as np
from sklearn.datasets import load_iris
from scipy.fftpack import fft

hello = 'world'
np.array([1, 2, 3])
load_iris(True)
fft()
print('')

def newTest(*b, a=2, d: int = 3, **c):
    b[2:3+3] = 4
    a = +3
    a = -3
    a = (b == 2)
    a = lambda x: x + 1
    
def yuki(args, **kwargs):
    a = 1 + 3.14
    return a

class Yui(object):
    def __init__(self, x):
        a = {
                'key': 'value',
                'yukino': 'yukinoshita'
            }
        pass
    
def testOperators():
    a = 1
    ccc = 'a string'
    a_very_long_variable_name_that_overflows = 1
    b = (ccc, (ccc, ccc))
    a + b
    a - b
    a * b
    a / b
    a ** b
    a // b
    a | b
    a & b
    a ^ b
    ~ a
    a % b
    a @ b
    a >> b
    a << b
    a < b
    a > b
    a == b
    a != b
    a >= b
    a <= b
    a += b
    a -= b
    a *= b
    a /= b
    a //= b
    a **= b
    a |= b
    a &= b
    a >>= b
    a <<= b
    a % b
    a @= b
    a ^= b
    
def pep8_indentation():
    # Aligned with opening delimiter.
    foo = long_function_name(var_one, var_two,
                             var_three, var_four)
    
    # More indentation included to distinguish this from the rest.
    def long_function_name(
            var_one, var_two, var_three,
            var_four):
        print(var_one)
        
    # Hanging indents should add a level.
    foo = long_function_name(
            var_one, var_two,
            var_three, var_four)
    
    my_list = [
            1, 2, 3,
            4, 5, 6,
            ]
    result = some_function_that_takes_arguments(
            'a', 'b', 'c',
            'd', 'e', 'f',
            )
    
    spam(ham[1], {eggs: 2})
    foo = (0,)
    if x == 4: print(x, y);x, y = y, x;
    ham[1:9], ham[1:9:3], ham[:9:3], ham[1:3], ham[1:9:]
    ham[lower:upper], ham[lower:upper:], ham[lower:step]
    dct['key'] = lst[index]
    
    def munge(input: AnyStr, sep: AnyStr = None, limit=1000) -> AnyStr:
        pass
    