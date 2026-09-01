#!/bin/bash
echo "KROK 3: ARCHIVÁCIA DOČASNÝCH SKRIPTOV"
cd ~/waste-platform || exit 1
mkdir -p scripts/archive
mv fix_*.sh diagnose_*.py run-*.sh finalize-everything.sh fix-waste-platform.sh fix_all.sh fix_database.sh start_app.sh scripts/archive/ 2>/dev/null
echo "HOTOVO."
