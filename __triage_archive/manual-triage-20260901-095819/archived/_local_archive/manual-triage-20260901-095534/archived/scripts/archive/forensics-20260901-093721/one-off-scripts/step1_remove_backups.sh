#!/bin/bash
echo "KROK 1: ODSTRAŇUJEM ZÁLOHY A DOČASNÉ SÚBORY"
cd ~/waste-platform || exit 1

# Odstránenie všetkých .bak, .backup, .bak-*, .orig, .old
find . -type f \( -name "*.bak" -o -name "*.backup" -o -name "*.bak-*" -o -name "*.orig" -o -name "*.old" \) -delete

# Odstránenie __pycache__ a .pyc
find . -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null
find . -name "*.pyc" -delete

# Odstránenie prázdnych adresárov
find . -type d -empty -delete

echo "HOTOVO. Zálohy a dočasné súbory boli odstránené."
