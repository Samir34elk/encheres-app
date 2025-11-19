import os

_extra_app_path = os.getenv("EXTRA_APP_PATH")
if _extra_app_path:
    candidate = os.path.join(_extra_app_path, "app")
    if os.path.isdir(candidate) and candidate not in __path__:
        __path__.append(candidate)
