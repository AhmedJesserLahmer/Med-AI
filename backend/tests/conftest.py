import os
import sys

# backend/ isn't a package (no __init__.py, matching the rest of the backend
# modules which import each other as plain top-level modules) so pytest's
# default rootdir insertion only adds backend/tests/ to sys.path. Add
# backend/ too, so tests can `import ranking`, `import schemas`, etc.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
