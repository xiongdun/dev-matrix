import pytest

from app.core.registry.base import Registry, register_in


class TestRegistry:
    def test_register_and_get(self):
        reg = Registry[object]()

        class Foo:
            pass

        reg.register("foo", Foo)
        assert reg.get("foo") is Foo

    def test_get_not_found(self):
        reg = Registry[object]()
        with pytest.raises(KeyError, match="Item 'missing' not found in registry"):
            reg.get("missing")

    def test_list(self):
        reg = Registry[object]()

        class Foo:
            pass

        class Bar:
            pass

        reg.register("foo", Foo)
        reg.register("bar", Bar)
        items = reg.list()
        assert items == {"foo": Foo, "bar": Bar}
        assert items is not reg._items

    def test_exists(self):
        reg = Registry[object]()

        class Baz:
            pass

        reg.register("baz", Baz)
        assert reg.exists("baz")
        assert not reg.exists("nonexistent")

    def test_unregister(self):
        reg = Registry[object]()

        class Qux:
            pass

        reg.register("qux", Qux)
        assert reg.exists("qux")
        reg.unregister("qux")
        assert not reg.exists("qux")

    def test_unregister_not_found(self):
        reg = Registry[object]()
        reg.unregister("nonexistent")
        assert not reg.exists("nonexistent")

    def test_get_type_error(self):
        reg = Registry[object]()
        with pytest.raises(TypeError, match="Registry name must be a string"):
            reg.get(123)

    def test_register_decorator(self):
        reg = Registry[object]()

        @register_in(reg, "my_class")
        class MyClass:
            pass

        assert reg.get("my_class") is MyClass

    def test_register_decorator_default_name(self):
        reg = Registry[object]()

        @register_in(reg)
        class AutoNamed:
            pass

        assert reg.get("AutoNamed") is AutoNamed
