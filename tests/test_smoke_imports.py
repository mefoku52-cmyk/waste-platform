import importlib
from pathlib import Path

root = Path("app/modules")
modules = []
for base in ("agent_platform", "lead_finder"):
    for p in (root / base).rglob("*.py"):
        rel = p.with_suffix("").relative_to(root)
        modules.append("app.modules." + str(rel).replace("/", "."))


def test_import_each_module():
    failures = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception as e:
            failures.append(f"{mod}: {type(e).__name__}: {e}")
    assert not failures, "Import failures:\n" + "\n".join(failures)
