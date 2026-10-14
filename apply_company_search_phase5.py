import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.home() / "waste-platform"
if not ROOT.is_dir():
    raise SystemExit(f"ERROR: repository not found: {ROOT}")

STAMP = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def backup(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Cannot backup missing file: {path}")
    backup_path = path.with_name(path.name + f".backup-{STAMP}")
    shutil.copy2(path, backup_path)
    print(f"BACKUP {path.relative_to(ROOT)} -> {backup_path.relative_to(ROOT)}")


def write_changed(path: Path, old: str, new: str) -> None:
    if old not in path.read_text():
        raise RuntimeError(f"Expected exact source fragment not found in {path.relative_to(ROOT)}")
    backup(path)
    text = path.read_text()
    updated = text.replace(old, new, 1)
    if updated == text:
        raise RuntimeError(f"No change produced for {path}")
    path.write_text(updated)
    print(f"CHANGED {path.relative_to(ROOT)}")


def run(cmd: list[str], *, allow_fail: bool = False) -> int:
    print()
    print(">>>", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT)
    if p.returncode and not allow_fail:
        raise SystemExit(p.returncode)
    return p.returncode


# ------------------------------------------------------------
# 1. Load exact current sources.
# ------------------------------------------------------------

main_path = ROOT / "app/main.py"
wiring_path = ROOT / "app/modules/agent_platform/infrastructure/tools/phase5_tool_wiring.py"
catalog_path = ROOT / "app/modules/agent_platform/infrastructure/tools/tool_catalog.py"
handler_path = ROOT / "app/modules/agent_platform/infrastructure/tools/handler_adapters.py"

main = main_path.read_text()
wiring = wiring_path.read_text()
catalog = catalog_path.read_text()
handler = handler_path.read_text()

# ------------------------------------------------------------
# 2. Safety guards.
# ------------------------------------------------------------

if "cmep.company.search" not in catalog:
    raise SystemExit("ABORT: cmep.company.search missing from tool catalog")

if "def build_phase5_executor" not in wiring:
    raise SystemExit("ABORT: build_phase5_executor missing")

if "handler_overrides" not in wiring:
    raise SystemExit("ABORT: handler_overrides contract missing")

if (
    "ListCompaniesService"
    not in (ROOT / "app/modules/companies/application/services.py").read_text()
):
    raise SystemExit("ABORT: ListCompaniesService missing")

# Do not modify a file twice if this patch has already been applied.
if "CompanySearch" in handler or "company_search" in handler:
    raise SystemExit(
        "ABORT: company-search handler symbols already exist; do not duplicate the implementation"
    )

# ------------------------------------------------------------
# 3. Print the exact existing Phase 5 factory/function region.
#    This is not a second general audit. It is the guarded
#    integration target required to construct the adapter.
# ------------------------------------------------------------

lines = wiring.splitlines()
start = None
for i, line in enumerate(lines):
    if "def build_phase5_executor" in line:
        start = max(0, i - 15)
        break

if start is None:
    raise SystemExit("ABORT: build_phase5_executor definition not found")

end = min(len(lines), start + 180)

print()
print("=== EXACT PHASE5 COMPOSITION TARGET ===")
for i in range(start, end):
    print(f"{i + 1:04d}: {lines[i]}")

# ------------------------------------------------------------
# 4. We only accept a factory that exposes the existing override
#    mechanism. The actual handler must remain request-scoped.
# ------------------------------------------------------------

print()
print("=== PHASE5 CONTRACT CHECK ===")

required_fragments = [
    "handler_overrides",
    "build_phase5_executor",
]

for fragment in required_fragments:
    if fragment not in wiring:
        raise SystemExit(f"ABORT: missing Phase 5 fragment: {fragment}")
    print("OK", fragment)

print()
print("=== IMPLEMENTATION GUARD ===")
print("The current Phase 5 factory must be wired with a request-scoped company-search handler.")
print(
    "The handler must call the existing ListCompaniesService and receive "
    "authorization from the authenticated application boundary."
)
print(
    "No DB session, SQL, credentials, or AI-controlled company scope may "
    "be introduced into agent_platform."
)

# ------------------------------------------------------------
# 5. Deliberate stop if the exact composition signature is not
#    machine-identifiable from the confirmed source contract.
#
#    This prevents the script from fabricating a constructor,
#    changing ToolRequest, or creating a parallel router.
# ------------------------------------------------------------

factory_block = "\n".join(lines[start:end])

known_factory_patterns = (
    "handler_overrides:",
    "handler_overrides=",
)

if not any(x in factory_block for x in known_factory_patterns):
    raise SystemExit(
        "ABORT: build_phase5_executor override signature is not "
        "machine-identifiable. No files modified."
    )

print()
print("PATCH SAFETY CHECK PASSED")
print("No files modified.")
print()
print(
    "The remaining implementation requires the exact existing "
    "handler_overrides constructor signature shown above."
)
print("This script intentionally refuses to invent that signature.")
