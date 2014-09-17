Observe arith.py and minmax.py, and compose unit test cases as following:

*   The unit test code for arith.py should be placed in test_arith.py, while the code for minmax.py should be placed in test_minmax.py.
*   Each function should be tested by an individual <code>unittest.TestCase</code>:
    -   <code>arith.add</code> should be tested by <code>test_arith.AddTestCase</code>.
    -   <code>arith.pow</code> should be tested by <code>test_arith.PowTestCase</code>.
    -   <code>minmax.get_min</code> should be tested by <code>test_minmax.GetMinTestCase</code>.
*   <code>test_arith.AddTestCase</code>:
    -   Method <code>test_positive_add_positive</code> to check the sum of two positive numbers.
    -   Method <code>test_positive_add_negative</code> to check the sum of a positive and a negative number.
    -   Method <code>test_negative_add_negative</code> to check the sum of two negative numbers.
*   <code>test_arith.PowTestCase</code>:
    -   Method <code>test_positive_pow_positive</code> to check the result of a positive number powered by another positive number.
    -   Method <code>test_positive_pow_negative</code> to check the result of a positive number powered by a negative number.
    -   Method <code>test_negative_pow_positive_success</code> to check the result of a negative number powered by a positive number, without <code>ValueError</code>.
    -   Method <code>test_negative_pow_positive_failure</code> to check the result of a negative number powered by a positive number, with <code>ValueError</code>.
    -   Method <code>test_negative_pow_negative_success</code> to check the result of a negative number powered by a negative number, without <code>ValueError</code>.
    -   Method <code>test_negative_pow_negative_failure</code> to check the result of a negative number powered by a negative number, with <code>ValueError</code>.
*   <code>test_arith.GetMinTestCase</code>:
    -   Method <code>test_abc</code> to check the result where a < b < c.
    -   Method <code>test_acb</code> to check the result where a < c < b.
    -   Method <code>test_bac</code> to check the result where b < a < c.
    -   Method <code>test_bca</code> to check the result where b < c < a.
    -   Method <code>test_cab</code> to check the result where c < a < b.
    -   Method <code>test_cba</code> to check the result where c < b < a.

You must make sure that your programs follow the code styles. Please upload your submission before deadlines. Otherwise there will be discounts on your scores.
