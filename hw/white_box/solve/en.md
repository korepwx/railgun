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
