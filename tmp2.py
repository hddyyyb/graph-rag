import sys
input = sys.stdin.readline

def solve():
    n, k = map(int, input().split())
    a = list(map(int, input().split()))
    def can(x):
        if x == 0:
            return True
        cnt = 0
        seen = [0]* x
        tag = 1
        have = 0
        for v in a:
            if 0 <= v < x:
                if seen[v] != tag:
                    seen[v] = tag
                    have += 1
                if have == x:
                    cnt += 1
                    if cnt >= k:
                        return True
                    tag += 1
                    have = 0
        return False
    left, right = 0, n//k
    ans = 0
    while left <= right:
        mid = (left + right)//2
        if can(mid):
            ans = mid
            left = mid + 1
        else:
            right = mid -1
    print(ans)
    
solve()