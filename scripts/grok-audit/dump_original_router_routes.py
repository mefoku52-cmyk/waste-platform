import sys
from pathlib import Path

project = Path.home() / "waste-platform"
sys.path.insert(0, str(project))

from app.main import create_app

app = create_app()

print("=== DUMP ORIGINAL ROUTER ROUTES ===")
for i, r in enumerate(app.routes, 1):
    if type(r).__name__ != "_IncludedRouter":
        continue

    print(f"[PARENT {i}] _IncludedRouter")

    if hasattr(r, "original_router"):
        try:
            orig = r.original_router
            print(f"  original_router_type={type(orig).__name__}")
            routes = getattr(orig, "routes", None)
            if routes:
                print(f"  original_router.routes count={len(routes)}")
                for j, nr in enumerate(routes, 1):
                    ncls = type(nr).__name__
                    npath = getattr(nr, "path", None)
                    nname = getattr(nr, "name", None)
                    nmethods = getattr(nr, "methods", None)
                    print(
                        f"    [{j}] {ncls} path={npath!r} name={nname!r} methods={sorted(nmethods) if nmethods else None}"
                    )
            else:
                print("  original_router.routes = None_or_empty")
        except Exception as e:
            print(f"  original_router ERROR: {e!r}")

    if hasattr(r, "effective_route_contexts"):
        try:
            ctx = r.effective_route_contexts
            print(f"  effective_route_contexts_type={type(ctx).__name__}")
            print(f"  effective_route_contexts_repr={repr(ctx)[:800]}")
        except Exception as e:
            print(f"  effective_route_contexts ERROR: {e!r}")

    print()
