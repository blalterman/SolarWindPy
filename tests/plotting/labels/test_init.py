import importlib.util
import sys
import types
from pathlib import Path


def _load_labels_module():
    """Load the labels module without importing the full package."""
    pkg_root = (
        Path(__file__).resolve().parents[3] / "solarwindpy" / "plotting" / "labels"
    )
    root_pkg = types.ModuleType("swlabels")
    root_pkg.__path__ = [str(pkg_root)]
    sys.modules["swlabels"] = root_pkg

    for name in (
        "base",
        "composition",
        "chemistry",
        "datetime",
        "elemental_abundance",
        "special",
    ):
        spec = importlib.util.spec_from_file_location(
            f"swlabels.{name}", pkg_root / f"{name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        module.__package__ = "swlabels"
        sys.modules[f"swlabels.{name}"] = module
        spec.loader.exec_module(module)

    spec = importlib.util.spec_from_file_location("swlabels", pkg_root / "__init__.py")
    labels = importlib.util.module_from_spec(spec)
    labels.__package__ = "swlabels"
    sys.modules["swlabels"] = labels
    spec.loader.exec_module(labels)
    return labels


def test_clean_str_list_for_printing():
    """Test grouping produced by ``_clean_str_list_for_printing``."""
    labels = _load_labels_module()
    data = ["beta", "alpha", "gamma", "Charlie"]
    result = labels._clean_str_list_for_printing(data)
    assert result.splitlines() == ["Charlie", "alpha", "beta", "gamma"]


def test_available_labels_output(capsys):
    """Check that ``available_labels`` prints all major sections.

    Parameters
    ----------
    capsys : pytest.CaptureFixture
        Pytest fixture used to capture standard output.
    """
    labels = _load_labels_module()
    labels.available_labels()
    captured = capsys.readouterr().out
    for section in (
        "TeXlabel knows",
        "Measurements",
        "Components",
        "Species",
        "Special",
    ):
        assert section in captured
