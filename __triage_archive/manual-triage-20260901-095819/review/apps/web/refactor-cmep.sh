#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

echo "[1/3] Presúvam backup súbory mimo src..."
mkdir -p backups/src-lib-api backups/src-lib-auth

if [ -d src/lib/api ]; then
  find src/lib/api -maxdepth 1 -type f -name '*.bak*' -print -exec mv {} backups/src-lib-api/ ;
fi

if [ -d src/lib/auth ]; then
  find src/lib/auth -maxdepth 1 -type f -name '*.bak*' -print -exec mv {} backups/src-lib-auth/ ;
fi

echo "[2/3] Vytváram public API index.ts pre feature moduly..."
mkdir -p src/features/{admin,auth,companies,compliance,documents,inquiries,listings,notifications,uploads}

cat > src/features/admin/index.ts <<'EOT'
export * from './api';
export * from './types';
export * from './hooks/use-admin-stats';
export * from './hooks/use-admin-users';
export * from './hooks/use-audit';
export * from './components/admin-users-table';
export * from './components/audit-table';
EOT

cat > src/features/auth/index.ts <<'EOT'
export * from './api';
export * from './types';
export * from './schemas';
export * from './hooks/use-auth-required';
export * from './hooks/use-current-user';
export * from './hooks/use-login';
export * from './hooks/use-logout';
export * from './hooks/use-register';
export * from './components/auth-bootstrap';
export * from './components/login-form';
export * from './components/register-form';
EOT

cat > src/features/companies/index.ts <<'EOT'
export * from './api';
export * from './types';
export * from './schemas';
export * from './hooks/use-companies';
export * from './hooks/use-company';
export * from './hooks/use-create-company';
export * from './components/companies-table';
export * from './components/company-form';
EOT

cat > src/features/compliance/index.ts <<'EOT'
export * from './api';
export * from './hooks/use-compliance';
export * from './hooks/use-create-compliance';
export * from './components/compliance-table';
EOT

cat > src/features/documents/index.ts <<'EOT'
export * from './api';
export * from './hooks/use-create-document';
export * from './hooks/use-documents';
export * from './components/document-form';
export * from './components/documents-table';
EOT

cat > src/features/inquiries/index.ts <<'EOT'
export * from './api';
export * from './hooks/use-inquiries';
export * from './components/inquiries-table';
export * from './components/open-inquiries-badge';
EOT

cat > src/features/listings/index.ts <<'EOT'
export * from './api';
export * from './types';
export * from './schemas';
export * from './hooks/use-create-listing';
export * from './hooks/use-listing';
export * from './hooks/use-listings';
export * from './hooks/use-marketplace';
export * from './hooks/use-matches';
export * from './components/listing-filters';
export * from './components/listing-form';
export * from './components/listings-table';
export * from './components/marketplace-table';
export * from './components/matches-panel';
EOT

cat > src/features/notifications/index.ts <<'EOT'
export * from './api';
export * from './hooks/use-notifications';
export * from './components/notifications-panel';
EOT

cat > src/features/uploads/index.ts <<'EOT'
export * from './api';
EOT

echo "[3/3] Prerábam app routy na route groups..."
mkdir -p src/app/'(public)' src/app/'(dashboard)'

for dir in login register forgot-password reset-password; do
  if [ -d "src/app/$dir" ] && [ ! -d "src/app/(public)/$dir" ]; then
    mv "src/app/$dir" "src/app/(public)/$dir"
  fi
done

if [ -d src/app/dashboard ] && [ ! -d "src/app/(dashboard)/dashboard" ]; then
  mv src/app/dashboard "src/app/(dashboard)/dashboard"
fi

echo
echo "Hotovo."
echo "Ďalší krok:"
echo "1) skontroluj tree src/app src/features | head -n 200"
echo "2) uprav importy na public API, napr.: from '@/features/auth'"
echo "3) spusť npm run lint && npm run typecheck"
