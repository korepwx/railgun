观察附件中 myfunc.py 中的函数 <code>myfunc</code>，写白盒测试，以达到尽可能高的覆盖率。

上交的代码必须符合相应语言的代码规范。请务必在截止日期前上交作业，否则有相应的评分折扣。

### myfunc.py: ###

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

### 参考解答 ###

```python
import unittest
from myfunc import myfunc


class SampleTestCase(unittest.TestCase):
    def test_abc(self):
        self.assertEqual(1, myfunc(1, 2, 3))

    def test_acb(self):
        self.assertEqual(1, myfunc(1, 3, 2))

    def test_bac(self):
        self.assertEqual(1, myfunc(2, 1, 3))

    def test_bca(self):
        self.assertEqual(1, myfunc(2, 3, 1))

    def test_cab(self):
        self.assertEqual(1, myfunc(3, 1, 2))

    def test_cba(self):
        self.assertEqual(1, myfunc(3, 2, 1))

``
