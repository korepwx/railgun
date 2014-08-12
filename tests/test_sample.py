import unittest
from sample import sample


class SampleTestCase(unittest.TestCase):
    def test_success(self):
        self.assertEqual(1, sample(1, 2, 3))

    def test_failure(self):
        self.assertEqual(1, sample(-1, -2, -3))

    def test_error(self):
        raise ValueError('This is test error.')

    @unittest.skip('Demonstration skipping')
    def test_skip(self):
        pass

    @unittest.expectedFailure
    def test_expectedFailure(self):
        self.assertEqual(5, sample(1, 2, 3))

    @unittest.expectedFailure
    def test_unexpectedSuccess(self):
        self.assertEqual(5, sample(5, 100, 200))
