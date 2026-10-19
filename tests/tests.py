import unittest
from object_accessor import Accessor


class TestAccessor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        pass
    
    def test_basic_initialization(self):
        """Test basic accessor initialization with different parameters."""
        # Test string initialization
        accessor = Accessor("user__profile__name")
        self.assertEqual(accessor, "user__profile__name")
        self.assertEqual(accessor.sep, "__")
        
        # Test with custom separator
        accessor = Accessor("user.profile.name", sep=".")
        self.assertEqual(accessor.sep, ".")
        
        # Test from another accessor (inheritance)
        original = Accessor("user__profile__name", ignore_callable=True)
        copy = Accessor(original)
        self.assertTrue(copy.ignore_callable)
    
    def test_keys_property(self):
        """Test the keys property returns correct split values."""
        accessor = Accessor("user__profile__name")
        self.assertEqual(accessor.keys, ("user", "profile", "name"))
        
        # Empty accessor
        accessor = Accessor("")
        self.assertEqual(accessor.keys, ())
    
    def test_get_next_object_dict_access(self):
        """Test dictionary-style key access in _get_next_object."""
        accessor = Accessor("user__profile__name")
        data = {"user": {"profile": {"name": "John"}}}
        
        # Test successful lookup
        result = accessor._get_next_object(data, "user")
        self.assertEqual(result, {"profile": {"name": "John"}})
        
        # Test nested lookup
        result = accessor._get_next_object({"profile": {"name": "John"}}, "profile")
        self.assertEqual(result, {"name": "John"})
    
    def test_get_next_object_attribute_access(self):
        """Test attribute access in _get_next_object."""
        class Person:
            def __init__(self):
                self.name = "John"
                
        class Address:
            def __init__(self):
                self.person = Person()
                
        accessor = Accessor("address__person__name")
        
        # Test attribute lookup
        result = accessor._get_next_object(Address(), "person")
        self.assertIsInstance(result, Person)
    
    def test_get_next_object_list_index_access(self):
        """Test list index access in _get_next_object."""
        accessor = Accessor("items__1")
        data = {"items": ["apple", "banana", "cherry"]}
        
        result = accessor._get_next_object(data, "1")
        self.assertEqual(result, "banana")
    
    def test_get_next_object_failure(self):
        """Test _get_next_object failure handling."""
        accessor = Accessor("nonexistent")
        data = {"user": "John"}
        
        # Test quiet mode (should return None)
        result = accessor._get_next_object(data, "missing", quiet=True)
        self.assertIsNone(result)
        
        # Test non-quiet mode (should raise ValueError)
        with self.assertRaises(ValueError):
            accessor._get_next_object(data, "missing", quiet=False)


if __name__ == '__main__':
    unittest.main()