import unittest
from decorator import validate_dict_types

class TestDictValidator(unittest.TestCase):

    @validate_dict_types
    def target_function(self, data: dict[str, int]):
        return True

    def test_valid_input(self):
        """Should pass with correct dict[str, int] types."""
        self.assertTrue(self.target_function({"apples": 5, "orages": 10}))

    def test_empty_dict(self):
        """Should pass with an empty dictionary."""
        self.assertTrue(self.target_function({}))

    def test_invalid_key_type(self):
        """Should raise TypeError if a key is not a string."""
        with self.assertRaisesRegex(TypeError, "Invalid key type"):
            self.target_function({1: 100})

    def test_invalid_value_type(self):
        """Should raise TypeError if a value is not an integer."""
        with self.assertRaisesRegex(TypeError, "Invalid value type"):
            self.target_function({"key": "100"})

    def test_mixed_invalid_types(self):
        """Should raise TypeError for float values."""
        with self.assertRaises(TypeError):
            self.target_function({"key": 1.5})

    def test_multiple_arguments(self):
        """Ensures the decorator handles multiple dictionary arguments."""
        @validate_dict_types
        def multi_arg_func(a: dict, b: dict):
            return True
        
        self.assertTrue(multi_arg_func({"a": 1}, {"b": 2}))
        with self.assertRaises(TypeError):
            multi_arg_func({"a": 1}, {"b": "invalid"})

if __name__ == "__main__":
    unittest.main()