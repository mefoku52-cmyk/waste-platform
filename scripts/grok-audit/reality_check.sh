#!/usr/bin/env bash
set -u

echo "=========================================="
echo "1. ZASTAVENIE VSETKYCH BEZIACICH R-GATE/PHASE SKRIPTOV"
echo "=========================================="
pkill -9 -f "phase_p0" 2>/dev/null && echo "zabite phase_p0 procesy" || echo "ziadne bezali"
pkill -9 -f "MASTER_DECISION_GATE" 2>/dev/null && echo "zabity gate proces" || echo "ziadny nebezal"
sleep 1
ps aux | grep -iE "phase_p0|decision_gate|closure_truth" | grep -v grep || echo "cisto - nic z toho nebezi"

echo ""
echo "=========================================="
echo "2. SME V SPRAVNOM PRIECINKU PROJEKTU?"
echo "=========================================="
cd ~/waste-platform 2>&1 || echo "CHYBA: ~/waste-platform neexistuje!"
pwd

echo ""
echo "=========================================="
echo "3. SKUTOCNY GIT STAV (nie z gate skriptu, priamo)"
echo "=========================================="
git status --short 2>&1 | wc -l
git log --oneline -5 2>&1
git branch --show-current 2>&1

echo ""
echo "=========================================="
echo "4. BEZIA SLUZBY TERAZ?"
echo "=========================================="
curl -s -o /dev/null -w "Backend: %{http_code}\n" http://localhost:8001/health 2>&1
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:3001 2>&1
ps aux | grep -E "uvicorn|next dev" | grep -v grep

echo ""
echo "=========================================="
echo "5. NEVYRIESENA VEC - SSH KLUC SUBORY V KORENI PROJEKTU"
echo "=========================================="
echo "--- Su v git? ---"
git ls-files 2>&1 | grep -i "ssh-ed25519"
echo "--- Obsah/velkost ---"
for f in ~/waste-platform/ssh-ed25519*; do
  if [ -f "$f" ]; then
    echo "SUBOR: $f"
    wc -l "$f" 2>&1
    wc -c "$f" 2>&1
  fi
done
echo "--- Existuju skutocne .ssh kluce niekde v $HOME? ---"
ls -la ~/.ssh/ 2>&1

echo ""
echo "=========================================="
echo "6. KOLKO R-GATE ARTEFAKTOV LEZI V PROJEKTE (len pocet, nemazat)"
echo "=========================================="
find ~/waste-platform -maxdepth 1 -iname "phase_p0*" 2>/dev/null | wc -l
find ~/waste-platform -maxdepth 1 -iname "*R1_R65*" -o -iname "*decision_gate*" -o -iname "*closure_truth*" 2>/dev/null | wc -l
find ~ -maxdepth 1 -iname "phase_P0*" -o -iname "*DECISION_GATE*" 2>/dev/null | wc -l

echo ""
echo "=========================================="
echo "7. JE SSH KLIENT DOSTUPNY (pre pripojenie na VPS)?"
echo "=========================================="
which ssh 2>&1
ssh -V 2>&1

echo ""
echo "=========================================="
echo "HOTOVO - toto je skutocny, priamo overeny stav"
echo "=========================================="
