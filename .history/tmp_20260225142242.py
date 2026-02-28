import time

def timer(func):
    def wrapper():
        start = time.time()
        func()
        print("耗时:", time.time() - start)
    return wrapper

@timer
def work():
    time.sleep(1)

work()