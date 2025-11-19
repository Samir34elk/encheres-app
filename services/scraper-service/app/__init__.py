import os
import sys

_extra_app_path = os.getenv("EXTRA_APP_PATH")
if _extra_app_path:
    candidate = os.path.join(_extra_app_path, "app")
    if os.path.isdir(candidate) and candidate not in __path__:
        __path__.append(candidate)
        if candidate not in sys.path:
            sys.path.append(candidate)

SCRIPTS_PATH = os.getenv("SCRIPTS_PATH", "/app/scripts")
if os.path.isdir(SCRIPTS_PATH) and SCRIPTS_PATH not in sys.path:
    sys.path.append(SCRIPTS_PATH)
