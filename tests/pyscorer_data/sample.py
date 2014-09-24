def sample(a, b, c):
    if a > b:
        if b > c:
            return c
        else:
            return b
    elif a > c:
        if c > b:
            return b
        else:
            return c
    else:
        return a
