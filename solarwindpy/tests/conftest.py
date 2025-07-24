import sys
import types
from pathlib import Path

pkg_path = Path(__file__).resolve().parent.parent
package = types.ModuleType("solarwindpy")
package.__path__ = [str(pkg_path)]
sys.modules.setdefault("solarwindpy", package)
