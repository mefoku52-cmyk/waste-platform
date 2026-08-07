#!/data/data/com.termux/files/usr/bin/bash

echo "===== PROJECT ====="
pwd

echo
echo "===== API ROUTER FILE ====="
ls -la app/shared/presentation/api_router.py
wc -l app/shared/presentation/api_router.py

echo
echo "===== MODULE ROUTERS ====="
find app/modules -path "*/presentation/router.py" -type f | sort

echo
echo "===== ROUTER CONTENTS ====="
for f in $(find app/modules -path "*/presentation/router.py" -type f | sort); do
    echo
    echo "######## $f ########"
    sed -n '1,180p' "$f"
done

echo
echo "===== SHARED PRESENTATION ====="
find app/shared/presentation -maxdepth 1 -type f | sort

echo
echo "===== API IMPORT REFERENCES ====="
grep -R "api_router\|include_router\|router =" -n app | head -200

echo
echo "===== FRONTEND FILES ====="
find apps/web -maxdepth 4 -type f | sort | head -200

echo
echo "===== GIT STATUS ====="
git status --short

