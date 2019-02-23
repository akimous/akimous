from matplotlib import pyplot as plt
from sympy import *
import time 
%matplotlib inline
'yoyoyo'
print('pppp')

plt.plot([1, 2], [3, 4])

time.sleep(3)

init_printing(use_latex=True)
x, y = symbols('x y')
expr = x + 2*y
expr