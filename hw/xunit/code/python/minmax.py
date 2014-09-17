def get_min(a, b, c):
    if (a < b):
        if (a < c):
            return a
        return c
    else:
        if (b < c):
            return b
        return c
