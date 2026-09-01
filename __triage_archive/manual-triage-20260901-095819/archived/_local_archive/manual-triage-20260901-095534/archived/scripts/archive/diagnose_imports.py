from __future__ import annotations

import importlib
import pkgutil
import traceback

PACKAGES = [
    "app.shared",
    "app.modules",
]


def modules(package_name: str):
    try:
        package = importlib.import_module(package_name)
    except Exception:
        traceback.print_exc()
        return

    if not hasattr(package, "__path__"):
        return

    for item in pkgutil.walk_packages(
        package.__path__,
        package.__name__ + ".",
    ):
        yield item.name


for package_name in PACKAGES:
    for module_name in modules(package_name) or []:
        try:
            importlib.import_module(module_name)
            print("OK  ", module_name)
        except Exception as exc:
            print("FAIL", module_name, "->", repr(exc))
