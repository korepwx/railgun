### test_arith.py:

```python
import unittest
from arith import add, pow


class AddTestCase(unittest.TestCase):

    def test_positive_add_positive(self):
        self.assertEqual(add(1, 2), 3)

    def test_positive_add_negative(self):
        self.assertEqual(add(1, -2), -1)

    def test_negative_add_negative(self):
        self.assertEqual(add(-1, -2), -3)


class PowTestCase(unittest.TestCase):

    def test_positive_pow_positive(self):
        self.assertEqual(pow(2, 3), 8)

    def test_positive_pow_negative(self):
        self.assertAlmostEqual(pow(2, -3), 0.125)

    def test_negative_pow_positive_success(self):
        self.assertEqual(pow(-2, 3), -8)

    def test_negative_pow_positive_failure(self):
        self.assertRaises(ValueError, pow, -4, 0.5)

    def test_negative_pow_negative_success(self):
        self.assertAlmostEqual(pow(-2, -3), -0.125)

    def test_negative_pow_negative_failure(self):
        self.assertRaises(ValueError, pow, -4, -0.5)

```

### test_minmax.py:

```python
import unittest
from minmax import get_min


class GetMinTestCase(unittest.TestCase):

    def test_abc(self):
        self.assertEqual(get_min(1, 2, 3), 1)

    def test_acb(self):
        self.assertEqual(get_min(1, 3, 2), 1)

    def test_bac(self):
        self.assertEqual(get_min(2, 1, 3), 1)

    def test_bca(self):
        self.assertEqual(get_min(3, 1, 2), 1)

    def test_cab(self):
        self.assertEqual(get_min(2, 3, 1), 1)

    def test_cba(self):
        self.assertEqual(get_min(3, 2, 1), 1)

```
