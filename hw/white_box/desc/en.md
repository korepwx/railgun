Observe function <code>myfunc</code> in myfunc.py. Write white-box unit tests and improve the coverage rate as you can.

Note that unit test classes in Python must inherit <code>unittest.TestCase</code>, and be placed in test_*.py files.

You must make sure that your programs follow the code styles. Please upload your handin before deadlines. Otherwise there will be discounts on your scores.

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

### Solution Example ###

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

```
