import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / "waste-platform"
if not ROOT.is_dir():
    raise SystemExit(f"ERROR: missing repository: {ROOT}")

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(path: Path) -> None:
    if path.exists():
        dst = path.with_name(path.name + f".backup-{STAMP}")
        shutil.copy2(path, dst)
        print(f"BACKUP {path} -> {dst}")


def fail(msg: str) -> None:
    raise SystemExit(f"PATCH_ABORTED: {msg}")


# ------------------------------------------------------------
# IMPORTANT:
# This patch deliberately refuses to guess the current source.
# It only proceeds when the expected Phase 5/company integration
# contracts are present in the actual checkout.
# ------------------------------------------------------------

required = [
    ROOT / "app/main.py",
    ROOT / "app/modules/companies/application/services.py",
    ROOT / "app/modules/companies/presentation/dependencies.py",
    ROOT / "app/modules/companies/presentation/router.py",
    ROOT / "app/modules/agent_platform/infrastructure/tools/tool_catalog.py",
    ROOT / "app/modules/agent_platform/infrastructure/tools/phase5_tool_wiring.py",
    ROOT / "app/modules/agent_platform/application/pipeline/agent_pipeline.py",
]

missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
if missing:
    fail("missing expected files: " + ", ".join(missing))

main = (ROOT / "app/main.py").read_text()
catalog = (ROOT / "app/modules/agent_platform/infrastructure/tools/tool_catalog.py").read_text()
wiring = (
    ROOT / "app/modules/agent_platform/infrastructure/tools/phase5_tool_wiring.py"
).read_text()
services = (ROOT / "app/modules/companies/application/services.py").read_text()
company_router = (ROOT / "app/modules/companies/presentation/router.py").read_text()

checks = {
    "company capability": "cmep.company.search" in catalog,
    "company search service": "ListCompaniesService" in services,
    "company route": "list_companies" in company_router,
}

for name, ok in checks.items():
    print(("CHECK_OK " if ok else "CHECK_FAIL ") + name)

if not all(checks.values()):
    fail("existing contract does not match the confirmed Phase 5/company architecture")

print()
print("=== CURRENT COMPOSITION ROOT ===")
print("app/main.py")
print()
print("=== EXISTING COMPANY CAPABILITY ===")
print("cmep.company.search")
print()
print("=== EXISTING BUSINESS SERVICE ===")
print("ListCompaniesService")
print()
print("=== EXISTING COMPANY API ===")
print("list_companies")
print()

# The actual source text is intentionally inspected before any mutation.
# If the current checkout has the expected wiring marker, the next step
# can be applied deterministically. Otherwise the script stops instead
# of silently inventing an integration point.

markers = [
    "include_router",
    "AgentRuntime",
    "phase5",
]

print("=== MAIN MARKERS ===")
for marker in markers:
    print(f"{marker}: {marker in main}")

print()
print("=== PHASE5 WIRING MARKERS ===")
for marker in (
    "build_phase5_executor",
    "cmep.company.search",
    "handler_overrides",
    "CallableToolHandler",
):
    print(f"{marker}: {marker in wiring}")

print()
print("=== DISCOVERY RESULT ===")
print("The checkout is structurally compatible with the confirmed company-search capability.")
print("No file has been modified by this script yet.")
print()
print("NEXT PATCH MUST TARGET ONLY THE EXACT CURRENT PHASE5 COMPOSITION SYMBOLS")
print("and must bind authorization at the authenticated application boundary.")
