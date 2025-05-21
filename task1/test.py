import unittest

from solution import strict, sum_two


class TestStrictDecorator(unittest.TestCase):

    def test_correct_type(self):
        self.assertEqual(sum_two(1, 2), 3)
        self.assertEqual(sum_two(-1, 2), 1)
        self.assertEqual(sum_two(0, 2), 2)

    def test_incorrect_types_in_args(self):
        with self.assertRaises(TypeError):
            sum_two(1, 2.4)
            sum_two(2.4, 100)
            sum_two(2.4, 3.1)
            sum_two("1", 2)
            sum_two(1, "2")
            sum_two("1", "2")
            sum_two(False, 2)
            sum_two(2, True)
            sum_two(False, True)

    def test_incorect_return_type(self):
        @strict
        def bad_return_func(a: int, b: int) -> int:
            return "bad"  # type: ignore

        with self.assertRaises(TypeError):
            bad_return_func(1, 2)

    def test_no_return_type(self):
        @strict
        def no_return_type(a: int, b: int):
            return a + b

        self.assertEqual(no_return_type(1, 2), 3)
        self.assertEqual(no_return_type(-1, 2), 1)

    def test_no_types(self):
        @strict
        def func_no_annotations(a, b):
            return a + b

        self.assertEqual(func_no_annotations(1, 2), 3)
        self.assertEqual(func_no_annotations(-1, 2), 1)
