import os
import sys
from importlib.machinery import ModuleSpec, SourceFileLoader
from pathlib import Path

# 1. Automatically ensure backend folder is in sys.path for both root and nested executions
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


# 2. Windows Smart App Control / WDAC Cython fallback hook:
# Transparently falls back to SQLAlchemy's bundled pure Python modules when
# newly unpacked unsigned .pyd extensions are blocked by Windows Application Control.
class _SmartAppControlPydFallback:
    def find_spec(self, fullname, path=None, target=None):
        if "sqlalchemy" in fullname and fullname.endswith(("_cy", "cy")):
            for p in path or []:
                py_path = os.path.join(p, fullname.split(".")[-1] + ".py")
                if os.path.isfile(py_path):
                    loader = SourceFileLoader(fullname, py_path)
                    return ModuleSpec(fullname, loader, origin=py_path)
        return None


if not any(isinstance(finder, _SmartAppControlPydFallback) for finder in sys.meta_path):
    sys.meta_path.insert(0, _SmartAppControlPydFallback())

# 3. Add system PostgreSQL libpq binaries to PATH for psycopg if present
libpq_dir = r"C:\Program Files\PostgreSQL\17\bin"
if os.path.isdir(libpq_dir) and libpq_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{libpq_dir};" + os.environ.get("PATH", "")

# Default to Python implementation of psycopg to avoid WDAC .pyd binary blocks
if "PSYCOPG_IMPL" not in os.environ:
    os.environ["PSYCOPG_IMPL"] = "python"
