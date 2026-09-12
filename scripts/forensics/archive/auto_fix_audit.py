#!/usr/bin/env python3
"""
Auto-generovaný fix skript pre Waste Platform
Vygenerovaný: Forenzný Audit v1.0
"""

import os

print("🔧 AUTO-FIX: Aplikujem opravy...")

# Fix 1: Vytvor chýbajúce __init__.py
missing_inits = [
    "app/__pycache__",
    "app/tests",
    "app/shared/__pycache__",
    "app/shared/presentation/__pycache__",
    "app/shared/domain/__pycache__",
    "app/shared/domain/ports/__pycache__",
    "app/shared/application/__pycache__",
    "app/shared/infrastructure/__pycache__",
    "app/shared/infrastructure/db/__pycache__",
    "app/shared/infrastructure/security/__pycache__",
    "app/modules/__pycache__",
    "app/modules/users/__pycache__",
    "app/modules/users/domain/__pycache__",
    "app/modules/users/application/__pycache__",
    "app/modules/users/infrastructure/__pycache__",
    "app/modules/users/presentation/__pycache__",
    "app/modules/auth/__pycache__",
    "app/modules/auth/domain/__pycache__",
    "app/modules/auth/application/__pycache__",
    "app/modules/auth/infrastructure/__pycache__",
    "app/modules/auth/presentation/__pycache__",
    "app/modules/companies/__pycache__",
    "app/modules/companies/domain/__pycache__",
    "app/modules/companies/application/__pycache__",
    "app/modules/companies/infrastructure/__pycache__",
    "app/modules/companies/presentation/__pycache__",
    "app/modules/company_memberships/__pycache__",
    "app/modules/company_memberships/domain/__pycache__",
    "app/modules/company_memberships/application/__pycache__",
    "app/modules/company_memberships/infrastructure/__pycache__",
    "app/modules/company_memberships/presentation/__pycache__",
    "app/modules/listings/__pycache__",
    "app/modules/listings/domain/__pycache__",
    "app/modules/listings/application/__pycache__",
    "app/modules/listings/infrastructure/__pycache__",
    "app/modules/listings/presentation/__pycache__",
    "app/modules/inquiries/__pycache__",
    "app/modules/inquiries/domain/__pycache__",
    "app/modules/inquiries/application/__pycache__",
    "app/modules/inquiries/infrastructure/__pycache__",
    "app/modules/inquiries/presentation/__pycache__",
    "app/modules/documents/__pycache__",
    "app/modules/documents/domain/__pycache__",
    "app/modules/documents/application/__pycache__",
    "app/modules/documents/infrastructure/__pycache__",
    "app/modules/documents/presentation/__pycache__",
    "app/modules/compliance/__pycache__",
    "app/modules/compliance/domain/__pycache__",
    "app/modules/compliance/application/__pycache__",
    "app/modules/compliance/infrastructure/__pycache__",
    "app/modules/compliance/presentation/__pycache__",
    "app/modules/notifications/__pycache__",
    "app/modules/notifications/domain/__pycache__",
    "app/modules/notifications/application/__pycache__",
    "app/modules/notifications/infrastructure/__pycache__",
    "app/modules/notifications/presentation/__pycache__",
    "app/modules/analytics/__pycache__",
    "app/modules/analytics/domain/__pycache__",
    "app/modules/analytics/application/__pycache__",
    "app/modules/analytics/infrastructure/__pycache__",
    "app/modules/analytics/presentation/__pycache__",
    "app/modules/admin/__pycache__",
    "app/modules/admin/domain/__pycache__",
    "app/modules/admin/application/__pycache__",
    "app/modules/admin/infrastructure/__pycache__",
    "app/modules/admin/presentation/__pycache__",
    "app/tests/unit",
    "app/tests/integration",
    "app/tests/unit/users",
    "app/tests/unit/companies",
    "app/tests/unit/auth",
    "app/core/__pycache__",
]
for path in missing_inits:
    init_file = os.path.join(path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write('"""Auto-generated."""\n')
        print(f"  ✅ {init_file}")

# Fix 2: Vytvor chýbajúce moduly z rozbitých importov
missing_modules = set()
missing_files = [
    "app/shared/domain/ports/clock.py",
    "app/shared/infrastructure/database.py",
]
for mf in missing_files:
    os.makedirs(os.path.dirname(mf), exist_ok=True)
    if not os.path.exists(mf):
        with open(mf, "w") as f:
            f.write('"""Auto-generated stub."""\n')
        print(f"  ✅ Stub: {mf}")

print("✅ Fixy aplikované. Spusti smoke test.")
