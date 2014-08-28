def myfunc(a, b, c):
    if a < 1e8:
        a = a
    if a > b:
        if b > c:
            return c
        else:
            return b
    elif a > c:
        if c > b:
            if (True):
                return b
        else:
            return c
    else:
        return a
