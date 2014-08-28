Observe function <code>myfunc</code> in myfunc.py. Write white-box unit tests and improve the coverage rate as you can.

Note that unit test classes in Python must inherit <code>unittest.TestCase</code>, and be placed in test_*.py files.

You must make sure that your programs follow the code styles. Please upload your submission before deadlines. Otherwise there will be discounts on your scores.

### myfunc.py: ###

```python
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
```
