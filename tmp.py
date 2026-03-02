import numpy as np


import sys

n = int(sys.stdin.readline())
res = []
for i in range(n):
    row = list(map(int,sys.stdin.readline().split()))
    res.append(row)

print(res)