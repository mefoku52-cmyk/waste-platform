#!/bin/bash
echo "KROK 2: ODSTRÁNENIE DUPLICITNÝCH models.py"
cd ~/waste-platform || exit 1

for mod in admin analytics compliance documents inquiries notifications; do
    if [ -f "app/modules/$mod/models.py" ] && [ -f "app/modules/$mod/infrastructure/models.py" ]; then
        echo "Odstraňujem app/modules/$mod/models.py"
        rm "app/modules/$mod/models.py"
    fi
done
echo "HOTOVO."
