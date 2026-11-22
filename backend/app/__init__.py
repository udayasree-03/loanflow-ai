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

# Windows WDAC xxhash fallback shim
try:
    import xxhash
    _ = xxhash.xxh3_128_hexdigest
except (ImportError, OSError, AttributeError):
    import hashlib
    import types

    def _to_bytes(data):
        if isinstance(data, str):
            return data.encode("utf-8")
        return bytes(data)

    class _PureHashWrapper:
        def __init__(self, data=b"", digest_size=16, seed=0):
            self._digest_size = digest_size
            self._h = hashlib.blake2b(digest_size=digest_size)
            if data:
                self._h.update(_to_bytes(data))

        def update(self, data):
            self._h.update(_to_bytes(data))
            return self

        def digest(self):
            return self._h.digest()

        def hexdigest(self):
            return self._h.hexdigest()

        def intdigest(self):
            return int.from_bytes(self._h.digest(), "big")

        def copy(self):
            c = _PureHashWrapper(digest_size=self._digest_size)
            c._h = self._h.copy()
            return c

    xxhash_mod = types.ModuleType("xxhash")
    xxhash_mod.xxh3_128 = lambda data=b"", seed=0: _PureHashWrapper(data, digest_size=16, seed=seed)
    xxhash_mod.xxh3_64 = lambda data=b"", seed=0: _PureHashWrapper(data, digest_size=8, seed=seed)
    xxhash_mod.xxh64 = lambda data=b"", seed=0: _PureHashWrapper(data, digest_size=8, seed=seed)
    xxhash_mod.xxh32 = lambda data=b"", seed=0: _PureHashWrapper(data, digest_size=4, seed=seed)

    xxhash_mod.xxh3_128_digest = lambda data=b"", seed=0: hashlib.blake2b(_to_bytes(data), digest_size=16).digest()
    xxhash_mod.xxh3_128_hexdigest = lambda data=b"", seed=0: hashlib.blake2b(_to_bytes(data), digest_size=16).hexdigest()
    xxhash_mod.xxh3_128_intdigest = lambda data=b"", seed=0: int.from_bytes(hashlib.blake2b(_to_bytes(data), digest_size=16).digest(), "big")

    xxhash_mod.xxh3_64_digest = lambda data=b"", seed=0: hashlib.blake2b(_to_bytes(data), digest_size=8).digest()
    xxhash_mod.xxh3_64_hexdigest = lambda data=b"", seed=0: hashlib.blake2b(_to_bytes(data), digest_size=8).hexdigest()
    xxhash_mod.xxh3_64_intdigest = lambda data=b"", seed=0: int.from_bytes(hashlib.blake2b(_to_bytes(data), digest_size=8).digest(), "big")

    xxhash_mod.xxh64_digest = xxhash_mod.xxh3_64_digest
    xxhash_mod.xxh64_hexdigest = xxhash_mod.xxh3_64_hexdigest
    xxhash_mod.xxh64_intdigest = xxhash_mod.xxh3_64_intdigest

    xxhash_mod.xxh32_digest = lambda data=b"", seed=0: hashlib.blake2b(_to_bytes(data), digest_size=4).digest()
    xxhash_mod.xxh32_hexdigest = lambda data=b"", seed=0: hashlib.blake2b(_to_bytes(data), digest_size=4).hexdigest()
    xxhash_mod.xxh32_intdigest = lambda data=b"", seed=0: int.from_bytes(hashlib.blake2b(_to_bytes(data), digest_size=4).digest(), "big")

    xxhash_mod.VERSION = "3.5.0"
    xxhash_mod.XXHASH_VERSION = "0.8.2"
    sys.modules["xxhash"] = xxhash_mod

