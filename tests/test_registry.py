import pytest

from app.core.registry.base import Registry, register_in


class TestRegistry:
    def test_register_and_get(self):
        reg = Registry[object]()

        class Foo:
            pass

        reg.register("foo", Foo)
        assert reg.get("foo") is Foo

    def test_get_missing_raises(self):
        reg = Registry[object]()
        with pytest.raises(KeyError):
            reg.get("missing")

    def test_exists(self):
        reg = Registry[object]()

        class Bar:
            pass

        reg.register("bar", Bar)
        assert reg.exists("bar")
        assert not reg.exists("baz")

    def test_unregister(self):
        reg = Registry[object]()

        class Baz:
            pass

        reg.register("baz", Baz)
        reg.unregister("baz")
        assert not reg.exists("baz")

    def test_register_decorator(self):
        reg = Registry[object]()

        @register_in(reg, "my_class")
        class MyClass:
            pass

        assert reg.get("my_class") is MyClass
