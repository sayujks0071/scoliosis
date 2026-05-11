import importlib


def test_cli_imports():
    mod = importlib.import_module("spinalmodes.cli")
    assert hasattr(mod, "cmd_figures")

