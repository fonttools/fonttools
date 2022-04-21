import dataclasses
import pytest

from fontTools.misc.configTools import (
    AbstractConfig,
    Option,
    Options,
    ConfigUnknownOptionError,
)


def test_can_create_custom_config_system():
    class MyConfig(AbstractConfig):
        options = Options()

    MyConfig.register_option(
        "test:option_name",
        "This is an option",
        0,
        int,
        lambda v: isinstance(v, int),
    )

    cfg = MyConfig({"test:option_name": "10"}, parse_values=True)

    assert 10 == cfg["test:option_name"]

    # This config is independent from "the" fontTools config
    with pytest.raises(ConfigUnknownOptionError):
        MyConfig({"fontTools.otlLib.optimize.gpos:COMPRESSION_LEVEL": 4})

    # Test the repr()
    assert repr(cfg) == "MyConfig({'test:option_name': 10})"

    # Test the skip_unknown param: just check that the following does not raise
    MyConfig({"test:unknown": "whatever"}, skip_unknown=True)

    # Test that it raises on unknown option
    with pytest.raises(ConfigUnknownOptionError):
        cfg.get("test:unknown")


def test_options_are_unique():
    class MyConfig(AbstractConfig):
        options = Options()

    opt1 = MyConfig.register_option("test:OPT_1", "", "foo", str, any)
    cfg = MyConfig({opt1: "bar"})
    assert cfg[opt1] == "bar"

    opt2 = Option("test:OPT_1", "", "foo", str, any)

    assert dataclasses.asdict(opt1) == dataclasses.asdict(opt2)
    assert opt1 != opt2

    with pytest.raises(ConfigUnknownOptionError):
        cfg.get(opt2)
    with pytest.raises(ConfigUnknownOptionError):
        cfg.set(opt2, "bar")


def test_optional_bool():
    for v in ("yes", "YES", "Yes", "1", "True", "true", "TRUE"):
        assert Option.parse_optional_bool(v) is True

    for v in ("no", "NO", "No", "0", "False", "false", "FALSE"):
        assert Option.parse_optional_bool(v) is False

    for v in ("auto", "AUTO", "Auto", "None", "none", "NONE"):
        assert Option.parse_optional_bool(v) is None

    with pytest.raises(ValueError, match="invalid optional bool"):
        Option.parse_optional_bool("foobar")

    assert Option.validate_optional_bool(True)
    assert Option.validate_optional_bool(False)
    assert Option.validate_optional_bool(None)
    assert not Option.validate_optional_bool(1)
    assert not Option.validate_optional_bool(0)
    assert not Option.validate_optional_bool("1")
