def decorator(func):
    def wrapper():
        print("执行前")
        func()
        print("执行后")
    return wrapper


@decorator
def hello():
    print("Hello!")

hello = decorator(hello)


hello()