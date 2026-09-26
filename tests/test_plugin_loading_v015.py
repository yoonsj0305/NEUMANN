import sys

from neumann1.plugin_loading import resolve_python_entry_point


def test_resolver_imports_only_when_called(tmp_path, monkeypatch):
    module_path = tmp_path / "temp_neumann_loader_probe.py"
    module_path.write_text(
        "VALUE = 41\n"
        "def factory():\n"
        "    return VALUE + 1\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("temp_neumann_loader_probe", None)

    assert "temp_neumann_loader_probe" not in sys.modules
    factory = resolve_python_entry_point("temp_neumann_loader_probe:factory")
    assert "temp_neumann_loader_probe" in sys.modules
    assert factory() == 42