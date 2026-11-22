import os
import sys

# Ensure backend directory and sitecustomize are loaded
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import sitecustomize  # noqa: F401 - activates WDAC Cython fallback
from alembic.config import main

if __name__ == "__main__":
    main()
