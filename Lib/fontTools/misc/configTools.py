"""
Code of the config system; not related to fontTools or fonts in particular.

The options that are specific to fontTools are in :mod:`fontTools.config`.

To create your own config system, you need to create an instance of
:class:`Options`, and a subclass of :class:`AbstractConfig` with its
``options`` class variable set to your instance of Options.

"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    Mapping,
    MutableMapping,
    Union,
)


log = logging.getLogger(__name__)

__all__ = [
    "AbstractConfig",
    "ConfigAlreadyRegisteredError",
    "ConfigError",
    "ConfigUnknownOptionError",
    "ConfigValueParsingError",
    "ConfigValueValidationError",
    "Option",
    "Options",
]


class ConfigError(Exception):
    """Base exception for the config module."""


class ConfigAlreadyRegisteredError(ConfigError):
    """Raised when a module tries to register a configuration option that
    already exists.

    Should not be raised too much really, only when developing new fontTools
    modules.
    """

    def __init__(self, name):
        super().__init__(f"Config option {name} is already registered.")


class ConfigValueParsingError(ConfigError):
    """Raised when a configuration value cannot be parsed."""

    def __init__(self, name, value):
        super().__init__(
            f"Config option {name}: value cannot be parsed (given {repr(value)})"
        )


class ConfigValueValidationError(ConfigError):
    """Raised when a configuration value cannot be validated."""

    def __init__(self, name, value):
        super().__init__(
            f"Config option {name}: value is invalid (given {repr(value)})"
        )


_NO_VALUE = object()


class ConfigUnknownOptionError(ConfigError):
    """Raised when a configuration option is unknown."""

    def __init__(self, name, value=_NO_VALUE):
        super().__init__(
            f"Config option {name} is unknown"
            + ("" if value is _NO_VALUE else f" (with given value {repr(value)})")
        )


@dataclass
class Option:
    help: str
    """Help text for this option."""
    default: Any
    """Default value for this option."""
    parse: Callable[[str], Any]
    """Turn input (e.g. string) into proper type. Only when reading from file."""
    validate: Callable[[Any], bool]
    """Return true if the given value is an acceptable value."""


class Options(Mapping):
    """Registry of available options for a given config system.

    Define new options using the :meth:`register()` method.

    Access existing options using the Mapping interface.
    """

    __options: Dict[str, Option]

    def __init__(self, other: "Options" = None) -> None:
        self.__options = {}
        if other is not None:
            for name, option in other.items():
                self.register_option(name, option)

    def register(
        self,
        name: str,
        help: str,
        default: Any,
        parse: Callable[[str], Any],
        validate: Callable[[Any], bool],
    ) -> Option:
        """Register a new option."""
        return self.register_option(name, Option(help, default, parse, validate))

    def register_option(self, name: str, option: Option) -> Option:
        """Register a new option."""
        if name in self.__options:
            raise ConfigAlreadyRegisteredError(name)
        self.__options[name] = option
        return option

    def __getitem__(self, key: str) -> Option:
        return self.__options.__getitem__(key)

    def __iter__(self) -> Iterator[str]:
        return self.__options.__iter__()

    def __len__(self) -> int:
        return self.__options.__len__()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({{\n"
            + "".join(
                f"    {k!r}: Option(default={v.default!r}, ...),\n"
                for k, v in self.__options.items()
            )
            + "})"
        )


_USE_GLOBAL_DEFAULT = object()


class AbstractConfig(MutableMapping):
    """
    Create a set of config values, optionally pre-filled with values from
    the given dictionary.

    .. seealso:: :meth:`set()`

    This config class is abstract because it needs its ``options`` class
    var to be set to an instance of :class:`Options` before it can be
    instanciated and used.

    .. code:: python

        class MyConfig(AbstractConfig):
            options = Options()

        MyConfig.register_option( "test:option_name", "This is an option", 0, int, lambda v: isinstance(v, int))

        cfg = MyConfig({"test:option_name": 10})
    """

    options: ClassVar[Options]

    @classmethod
    def register_option(cls, *args, **kwargs) -> Option:
        """Register an available option in this config system."""
        return cls.options.register(*args, **kwargs)

    _values: Dict[str, Any]

    def __init__(
        self,
        values: Union[AbstractConfig, Dict] = {},
        parse_values=False,
        skip_unknown=False,
    ):
        self._values = {}
        values_dict = values._values if isinstance(values, AbstractConfig) else values
        for name, value in values_dict.items():
            self.set(name, value, parse_values, skip_unknown)

    def set(self, name: str, value: Any, parse_values=False, skip_unknown=False):
        """Set the value of an option.

        Args:
            * `parse_values`: parse the configuration value from a string into
                its proper type, as per its `Option` object. The default
                behavior is to raise `ConfigValueValidationError` when the value
                is not of the right type. Useful when reading options from a
                file type that doesn't support as many types as Python.
            * `skip_unknown`: skip unknown configuration options. The default
                behaviour is to raise `ConfigUnknownOptionError`. Useful when
                reading options from a configuration file that has extra entries
                (e.g. for a later version of fontTools)
        """
        try:
            option = self.options[name]
        except KeyError:
            if skip_unknown:
                log.debug(
                    "Config option %s is unknown (with given value %r)", name, value
                )
                return
            else:
                raise ConfigUnknownOptionError(name, value)

        # Can be useful if the values come from a source that doesn't have
        # strict typing (.ini file? Terminal input?)
        if parse_values:
            try:
                value = option.parse(value)
            except Exception as e:
                raise ConfigValueParsingError(name, value) from e

        if not option.validate(value):
            raise ConfigValueValidationError(name, value)

        self._values[name] = value

    def get(self, name: str, default=_USE_GLOBAL_DEFAULT):
        """
        Get the value of an option. The value which is returned is the first
        provided among:

        1. a user-provided value in the options's ``self._values`` dict
        2. a caller-provided default value to this method call
        3. the global default for the option provided in ``fontTools.config``

        This is to provide the ability to migrate progressively from config
        options passed as arguments to fontTools APIs to config options read
        from the current TTFont, e.g.

        .. code:: python

            def fontToolsAPI(font, some_option):
                value = font.cfg.get("someLib.module:SOME_OPTION", some_option)
                # use value

        That way, the function will work the same for users of the API that
        still pass the option to the function call, but will favour the new
        config mechanism if the given font specifies a value for that option.
        """
        if name in self._values:
            return self._values[name]
        if default is not _USE_GLOBAL_DEFAULT:
            return default
        try:
            return self.options[name].default
        except KeyError as e:
            raise ConfigUnknownOptionError(name) from e

    def copy(self):
        return self.__class__(self._values)

    def __getitem__(self, name: str) -> Any:
        return self.get(name)

    def __setitem__(self, name: str, value: Any) -> None:
        return self.set(name, value)

    def __delitem__(self, name: str) -> None:
        del self._values[name]

    def __iter__(self) -> Iterator:
        return self._values.__iter__()

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self._values)})"
