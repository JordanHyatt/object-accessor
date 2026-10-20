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
        
        result = accessor._get_next_object(data["items"], "1")
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

    def test_resolve(self):
        """Test the resolve method with various scenarios."""
        
        # Test basic dictionary access
        accessor = Accessor("user__profile__name")
        data = {"user": {"profile": {"name": "John"}}}
        result = accessor.resolve(data)
        self.assertEqual(result, "John")
        
        # Test attribute access
        class Person:
            def __init__(self):
                self.name = "John"
                
        class Address:
            def __init__(self):
                self.person = Person()
                
        accessor = Accessor("person__name")
        result = accessor.resolve(Address())
        self.assertEqual(result, "John")
        
        # Test list index access
        accessor = Accessor("items__1")
        data = {"items": ["apple", "banana", "cherry"]}
        result = accessor.resolve(data)
        self.assertEqual(result, "banana")
        
        # Test mixed access patterns
        class User:
            def __init__(self):
                self.profile = {"name": "Jane"}
                
        class Data:
            def __init__(self):
                self.users = [User(), User()]
                
        accessor = Accessor("users__0__profile__name")
        result = accessor.resolve(Data())
        self.assertEqual(result, "Jane")
        
        # Test with custom separator
        accessor = Accessor("user.profile.name", sep=".")
        data = {"user": {"profile": {"name": "Alice"}}}
        result = accessor.resolve(data)
        self.assertEqual(result, "Alice")
        
        # Test quiet mode (should return None on failure)
        accessor = Accessor("nonexistent")
        data = {"user": "John"}
        result = accessor.resolve(data, quiet=True)
        self.assertIsNone(result)
        
        # Test with default value
        accessor = Accessor("nonexistent")
        data = {"user": "John"}
        result = accessor.resolve(data, quiet=True, default="Not found")
        self.assertEqual(result, "Not found")
        
        # Test callable handling (ignore_callable=False by default)
        def get_name():
            return "Callable Name"
            
        accessor = Accessor("get_name")
        data = {"get_name": get_name}
        result = accessor.resolve(data)
        self.assertEqual(result, "Callable Name")
        
        # Test with ignore_callable=True
        accessor = Accessor("get_name", ignore_callable=True)
        data = {"get_name": get_name}
        result = accessor.resolve(data)
        # Should return the function object itself since it's ignored
        self.assertIs(result, get_name)
        
        # Test empty accessor
        accessor = Accessor("")
        data = {"user": "John"}
        result = accessor.resolve(data)
        self.assertEqual(result, data)
        
        # Test single key accessor
        accessor = Accessor("user")
        data = {"user": "John"}
        result = accessor.resolve(data)
        self.assertEqual(result, "John")

        # Test django specific call_callable override
        def func():
            return 'CALLED'
        data = {'key':func}
        r = Accessor('key').resolve(data)
        self.assertEqual(r, 'CALLED')
        func.do_not_call_in_templates = True
        data = {'key':func}
        r = Accessor('key').resolve(data)
        self.assertEqual(r, func)

if __name__ == '__main__':
    unittest.main()