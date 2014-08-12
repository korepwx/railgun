观察附件中 myfunc.py 中的函数 <code>myfunc</code>，写白盒测试，以达到尽可能高的覆盖率。

上交的代码必须符合相应语言的代码规范。请务必在截止日期前上交作业，否则有相应的评分折扣。

myfunc.py:

```python
def myfunc(a, b, c):
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
```
