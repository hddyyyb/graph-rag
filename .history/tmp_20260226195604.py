# m* n的整数矩阵
# 其实坐标 i，j
# 可以走上下左右四个方向
# 下一个点对应证书矩阵的值更大
# 重复到不能走为止
# 输出长度最长的路径

d = [[1,2,3],[4,5,6]]
m = len(d)
n = len(d[0])
res = 0
direction = (0,1), (1, 0), (0, -1), (-1, 0)

def dfs(i, j, basic, l):
    if i >= m or i < 0 or j >=n or j < 0:
        return
    if d[i][j] <= basic:
        return
    
    res = max(res, l)
    for di, dj in direction:
        i1= i + di
        j1 = j + dj
        dfs(i1, j1, d[i][j], l+1)
    

for i in range(m):
    for j in range(n):
        dfs(i,j)

print(res) 


