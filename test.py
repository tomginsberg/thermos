# write a function to test if a number is prime
def is_prime(num):
    for i in range(2, num):
        if num % i == 0:
            print(num, "is not a prime number")
            print(i, "times", num // i, "is", num)
            return False
    else:
        return True


# write some tests
import unittest


class TestPrime(unittest.TestCase):

    def test_prime(self):
        self.assertEqual(is_prime(11), True)

    def test_not_prime(self):
        self.assertEqual(is_prime(4), False)

    def test_zero(self):
        self.assertEqual(is_prime(0), False)
