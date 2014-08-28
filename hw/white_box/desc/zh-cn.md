观察附件中 myfunc.py 中的函数 <code>myfunc</code>，写白盒单元测试，以达到尽可能高的覆盖率。

注意在 Python 中单元测试的类型必须继承自 <code>unittest.TestCase</code>，并且以保存在 test_*.py 的文件中。

上交的代码必须符合相应语言的代码规范。请务必在截止日期前上交作业，否则有相应的评分折扣。

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
