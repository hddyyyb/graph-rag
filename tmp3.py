import sys
import heapq

input = sys.stdin.readline

def solve():
    n = int(input())
    jobs = []
    for _ in range(n):
        a, b = map(int, input().split())
        jobs.append((b,a))
    jobs.sort()
    heap = []
    total_time = 0
    processed = 0
    ans = 0
    m = len(jobs)
    i = 0
    prev_deadline = 0
    while i < m:
        d = jobs[i][0]
        if prev_deadline != 0 and d > prev_deadline +1:
            unhappy = processed - len(heap)
            ans += unhappy* (d - prev_deadline - 1)
        
        while i < m and jobs[i][0] == d:
            b, a = jobs[i]
            processed += 1
            total_time += a
            heapq.heappush(heap, -a)
        
            if total_time > d:
                longest = -heapq.heappop(heap)
                total_time -= longest

            i += 1
    
        unhappy = processed - len(heap)
        ans += unhappy
        prev_deadline = d
    
    print(ans)

    
solve()