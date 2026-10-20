import re

class Accessor(str):
    """
    A string describing a path from one object to another via attribute/index
    accesses. For convenience, the class has an alias `.A` to allow for more concise code.

    Relations are separated by a ``__`` character.

    To support list-of-dicts from ``QuerySet.values()``, if the context is a dictionary,
    and the accessor is a key in the dictionary, it is returned right away.
    
    Keys that match the pattern ``--\w+--`` (dunder patterns) are automatically converted
    to ``__`` format before lookup. This allows for "Dunder" attributes that conflict with 
    the dunder seperater can be represented as double dash "--"
    """

    DEFAULT_SEPARATOR = "__"
    DUNDER_PATTERN = re.compile(r"--\w+--")

    ALTERS_DATA_ERROR_FMT = "Refusing to call {method}() because `.alters_data = True`"
    LOOKUP_ERROR_FMT = (
        "Failed lookup for key [{key}] in {context}, when resolving the accessor {accessor}"
    )

    def __init__(
        self, 
        value, 
        sep=DEFAULT_SEPARATOR,
        callable_kwargs=None, 
        ignore_callable=False,
        ignore_callable_until_end=False,
    ):
        """
        Initialize an Accessor instance with a path value and configuration options.
        
        The Accessor class represents a path from one object to another via attribute/index
        accesses. It can be initialized with a string path or another Accessor instance.
        
        When initialized with another Accessor instance, it inherits the configuration
        settings from the source accessor, allowing for easy modification of accessors
        while preserving their behavior.
        
        Example usage:
            >>> from object_accessor import Accessor
            
            >>> # Initialize with a string path
            >>> accessor = Accessor("user__profile__name")
            >>> print(accessor)
            'user__profile__name'
            
            >>> # Initialize with custom separator
            >>> accessor = Accessor("user.profile.name", sep=".")
            >>> print(accessor.sep)
            '.'
            
            >>> # Initialize with callable kwargs
            >>> accessor = Accessor("user__get_data", callable_kwargs={"param": "value"})
            >>> print(accessor.callable_kwargs)
            {'param': 'value'}
            
            >>> # Initialize from another accessor (inherits settings)
            >>> original = Accessor("user__profile__name", ignore_callable=True)
            >>> copy = Accessor(original)
            >>> print(copy.ignore_callable)
            True
            
        Args:
            value: The path value to initialize with. Can be a string or another Accessor instance.
            sep: The separator character used to split the accessor path. Defaults to '__'.
            callable_kwargs: Keyword arguments to pass when calling callables during resolution.
            ignore_callable: If True, callable objects will not be invoked during resolution.
            ignore_callable_until_end: If True, callable objects are ignored until the final key
                                      in the accessor path. This is useful for cases where
                                      you want to call a function at the end of the chain but
                                      not earlier steps.

        Note:
            - When `ignore_callable` and `ignore_callable_until_end` are both False,
              callables are invoked only on the final key of the accessor path.
            - When `ignore_callable` is True, all callable invocations are skipped.
            - When `ignore_callable_until_end` is True, callables are skipped until the last key
              in the path, then invoked if callable.
        """
        self.sep = getattr(value, 'sep', None) or sep
        self.callable_kwargs = callable_kwargs or getattr(value, "callable_kwargs", None) or {}
        if isinstance(value, self.__class__):
            self.ignore_callable = getattr(value, 'ignore_callable')
            self.ignore_callable_until_end = getattr(value, 'ignore_callable_until_end')
        else:
            self.ignore_callable = ignore_callable
            self.ignore_callable_until_end = ignore_callable_until_end
        super().__init__()

    def __new__(cls, value, **kwargs):
        instance = super().__new__(cls, value)
        return instance

    @property
    def keys(self):
        if self == "":
            return ()
        return tuple(self.split(self.sep))

    def _get_next_object(self, obj, next_key, call_callable=False, callable_kwargs=None, quiet=False):
        """
        Get the next object in the accessor chain by attempting multiple lookup methods.
        
        This method tries to resolve the next object in a path by checking:
        1. Dictionary-style key access (obj[next_key])
        2. Attribute access (getattr(obj, next_key))
        3. List index access (obj[int(next_key)])
        
        If the lookup fails and quiet=False, a ValueError is raised with context about
        the failed lookup. If call_callable is True and the resolved object is callable,
        it will be invoked with the provided callable_kwargs.
        
        Keys that match the pattern ``--\w+--`` (dunder patterns) are automatically converted
        to ``__`` format before lookup. This allows for compatibility with Django's 
        QuerySet.values() which returns keys with double underscore prefixes and suffixes, 
        as well as "dunder attributes" such as __class__
        
        Args:
            obj: The current object to perform lookups on
            next_key: The key/index/attribute name to look up
            call_callable: If True and the resolved object is callable, invoke it
            callable_kwargs: Keyword arguments to pass when calling a callable
            quiet: If True, don't raise exceptions on lookup failure
            
        Returns:
            The resolved object or None if not found and quiet=True
            
        Raises:
            ValueError: When lookup fails and quiet=False
        """
        if obj == None:
            return obj
        callable_kwargs = callable_kwargs or {}
        if bool(self.DUNDER_PATTERN.match(next_key)):
            next_key = next_key.replace('--', self.sep)
        # First Try Dictionary lookup
        try: 
            next_obj = obj[next_key]
        except (
            IndexError,  # list index out of range
            ValueError,  # invalid literal for int()
            KeyError,  # dict without `int(bit)` key
            TypeError,  # unsubscriptable object
        ):
            next_obj = None
        if next_obj == None:
            # Next try attribute lookup
            next_obj = getattr(obj, next_key, None)
        if next_obj == None:
            # last try list index lookup
            try: 
                next_obj = obj[int(next_key)]
            except (
                IndexError,  # list index out of range
                ValueError,  # invalid literal for int()
                KeyError,  # dict without `int(bit)` key
                TypeError,  # unsubscriptable object
            ):
                next_obj = None
        if next_obj == None and not quiet:
            raise ValueError(
                self.LOOKUP_ERROR_FMT.format(key=next_key, context=obj, accessor=self)
            )
        if next_obj == None:
            return next_obj
        if call_callable and callable(next_obj):
            return next_obj(**callable_kwargs)
        return next_obj

    def resolve(self, obj, quiet=True, default=None):
        """
        Resolve the accessor path against the given object and return the final value.
        
        This method traverses the accessor path (split by the separator '__') step by step,
        applying the appropriate lookup methods for each key in the path. The traversal
        continues until all keys are processed or an error occurs.
        
        Keys that match the pattern ``--\w+--`` (dunder patterns) are automatically converted
        to ``__`` format before lookup. This allows for compatibility with Django's 
        QuerySet.values() which returns keys with double underscore prefixes and suffixes.
        
        Example usage:
            >>> from object_accessor import Accessor
            >>> # Simple attribute access
            >>> class Person:
            ...     def __init__(self):
            ...         self.name = "John"
            ... 
            >>> person = Person()
            >>> accessor = Accessor("name")
            >>> accessor.resolve(person)
            'John'
            
            >>> # Nested attribute access
            >>> class Address:
            ...     def __init__(self):
            ...         self.street = "123 Main St"
            ... 
            >>> class Person:
            ...     def __init__(self):
            ...         self.name = "John"
            ...         self.address = Address()
            ... 
            >>> person = Person()
            >>> accessor = Accessor("address__street")
            >>> accessor.resolve(person)
            '123 Main St'
            
            >>> # Dictionary access
            >>> data = {"user": {"name": "Jane"}}
            >>> accessor = Accessor("user__name")
            >>> accessor.resolve(data)
            'Jane'
            
            >>> # List indexing
            >>> data = {"items": ["apple", "banana", "cherry"]}
            >>> accessor = Accessor("items__1")
            >>> accessor.resolve(data)
            'banana'
            
            >>> # Callable handling (when ignore_callable=False)
            >>> def get_name():
            ...     return "Callable Name"
            >>> data = {"get_name": get_name}
            >>> accessor = Accessor("get_name")  # This will call the function
            >>> accessor.resolve(data)
            'Callable Name'
            
        Args:
            obj: The object to resolve the accessor path against
            quiet: If True, suppress exceptions and return None on lookup failure.
                   If False, raise ValueError on lookup failure.
            default: The default value to return if resolution fails and quiet=True
            
        Returns:
            The resolved value from the accessor path, or None/default if not found
            and quiet=True, or raises an exception if quiet=False and lookup fails
            
        Example:
            >>> from object_accessor import Accessor
            >>> # Create an accessor for nested data
            >>> accessor = Accessor("user__profile__name")
            >>> data = {"user": {"profile": {"name": "Alice"}}}
            >>> result = accessor.resolve(data)
            >>> print(result)
            'Alice'
        """
        current = obj
        keys = self.keys
        len_keys = len(keys)
        try:
            for i,key in enumerate(keys, start=1):
                last_key = i == len_keys
                if last_key:
                    call_callable = (not self.ignore_callable or self.ignore_callable_until_end)
                else:
                    call_callable = not self.ignore_callable
                current = self._get_next_object(obj=current, next_key=key, call_callable=call_callable, callable_kwargs=self.callable_kwargs, quiet=quiet)
                if current is None:
                    current = default
                    break
            return current
        except Exception:
            if not quiet:
                raise
            return default
