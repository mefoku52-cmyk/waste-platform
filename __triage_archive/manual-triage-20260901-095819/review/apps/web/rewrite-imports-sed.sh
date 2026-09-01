#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

find src -type f ( -name '*.ts' -o -name '*.tsx' ) \
  ! -path '*/node_modules/*' \
  -print0 |
while IFS= read -r -d '' file; do
  sed -Ei \
    -e "s#@/features/admin/[^"']+#@/features/admin#g" \
    -e "s#@/features/auth/[^"']+#@/features/auth#g" \
    -e "s#@/features/companies/[^"']+#@/features/companies#g" \
    -e "s#@/features/compliance/[^"']+#@/features/compliance#g" \
    -e "s#@/features/documents/[^"']+#@/features/documents#g" \
    -e "s#@/features/inquiries/[^"']+#@/features/inquiries#g" \
    -e "s#@/features/listings/[^"']+#@/features/listings#g" \
    -e "s#@/features/notifications/[^"']+#@/features/notifications#g" \
    -e "s#@/features/uploads/[^"']+#@/features/uploads#g" \
    "$file"
done

echo "Hotovo. Skontroluj diff a spusti npm run lint && npm run typecheck"
