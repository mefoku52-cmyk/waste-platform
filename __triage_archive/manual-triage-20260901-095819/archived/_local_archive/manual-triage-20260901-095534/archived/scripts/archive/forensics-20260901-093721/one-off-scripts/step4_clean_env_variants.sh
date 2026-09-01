#!/bin/bash
echo "KROK 4: VYČISTENIE .env VARIANTOV"
cd ~/waste-platform || exit 1
rm -f .env.bak* .env.*.bak .env.*.backup .env.production.example .env.local.template 2>/dev/null
if [ ! -f .env.example ] && [ -f .env ]; then
    cp .env .env.example
    sed -i 's/^\(.*=\)\(.*\)$/\1<CHANGE_ME>/g' .env.example
fi
echo "HOTOVO."
