# Object Accessor

A Python library for navigating nested data structures using simple accessor paths. The library provides a clean, intuitive way to access nested attributes, dictionary keys, and list indices through a unified interface.

## Features

- **Nested Access**: Navigate deeply nested objects using simple path notation (e.g., `user__profile__name`)
- **Flexible Separators**: Support for custom separators (default is `__`)
- **Dictionary & Attribute Access**: Automatically handles both dictionary key access and attribute access
- **List Indexing**: Supports list and tuple indexing via string indices (e.g., `items__1`)
- **Callable Handling**: Option to call functions at the end of accessor chains or ignore them entirely

## Inspiration

This library was inspired by the `Accessor` util in the  [django-tables2](https://github.com/jieter/django-tables2) project

## Installation

```bash
pip install object-accessor
```

## Quick Start

```python
from object_accessor import Accessor

# Basic usage with default separator (__)
accessor = Accessor("user__profile__name")
data = {"user": {"profile": {"name": "John"}}}
result = accessor.resolve(data)
print(result)  # Output: John

# Using custom separator (.)
accessor = Accessor("user.profile.name", sep=".")
data = {"user": {"profile": {"name": "Jane"}}}
result = accessor.resolve(data)
print(result)  # Output: Jane

# List indexing
accessor = Accessor("items__1")
data = {"items": ["apple", "banana", "cherry"]}
result = accessor.resolve(data)
print(result)  # Output: banana

# Attribute access
class Person:
    def __init__(self):
        self.name = "John"
        
class Address:
    def __init__(self):
        self.person = Person()

accessor = Accessor("person__name")
result = accessor.resolve(Address())
print(result)  # Output: John

#  "Dunder" attributes that conflict with the dunder seperater can be represented as double dash "--"

accessor = Accessor("person__--class--", ignore_callables=True)
result = accessor.resolve(Address())
print(result)  # Output: <class '__main__.Person'>

```

## Usage Examples

### Basic Accessor Creation

```python
from object_accessor import Accessor

# Create accessors with different configurations
accessor1 = Accessor("user__profile__name")  # Default separator (__)
accessor2 = Accessor("user.profile.name", sep=".")  # Custom separator (.)
accessor3 = Accessor(accessor1)  # Copy from existing accessor
```

### Handling Callables

```python
# Callable handling - by default, functions are called
def get_user():
    return "Alice"

accessor = Accessor("get_user")
data = {"get_user": get_user}
result = accessor.resolve(data)
print(result)  # Output: Alice

# Ignore callable behavior
accessor = Accessor("get_user", ignore_callable=True)
result = accessor.resolve(data)
print(result)  # Output: <function get_user at 0x...>
```

### Error Handling

```python
# Quiet mode (returns None on failure)
accessor = Accessor("nonexistent")
data = {"user": "John"}
result = accessor.resolve(data, quiet=True)
print(result)  # Output: None

# Default value support
result = accessor.resolve(data, quiet=True, default="Not found")
print(result)  # Output: Not found

# Non-quiet mode (raises exception on failure)
try:
    accessor.resolve(data, quiet=False)
except ValueError as e:
    print(e)  # Raises exception
```

## API Reference

### Accessor Class

**`Accessor(value, sep=DEFAULT_SEPARATOR, callable_kwargs=None, ignore_callable=False, ignore_callable_until_end=False)`**

Initialize an Accessor instance.

- `value`: The path value to initialize with (string or another Accessor)
- `sep`: Separator character used to split the accessor path (default: `__`)
- `callable_kwargs`: Keyword arguments passed when calling callables during resolution
- `ignore_callable`: If True, callable objects will not be invoked during resolution
- `ignore_callable_until_end`: If True, callable objects are ignored until the final key in the path

### Methods

**`resolve(obj, quiet=False, default=None)`**

Resolve the accessor path against the given object.

- `obj`: The object to resolve the accessor path against
- `quiet`: If True, suppress exceptions and return None on lookup failure
- `default`: Default value to return if resolution fails and quiet=True

**`keys`**

Property that returns the split keys of the accessor path as a tuple.

## License

MIT License
