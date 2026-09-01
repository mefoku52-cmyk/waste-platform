#!/data/data/com.termux/files/usr/bin/bash
set -e
echo "PWD: $(pwd)"
echo
echo "== config files =="
find . -maxdepth 3 ( -name "package.json" -o -name "docker-compose.yml" -o -name "compose.yaml" -o -name "requirements.txt" -o -name "pyproject.toml" -o -name "vite.config.*" -o -name "next.config.*" ) | sort
echo
echo "== package scripts =="
find . -maxdepth 3 -name package.json -exec sh -c '
  f="$1"
  echo
  echo "### $f"
  sed -n "1,220p" "$f"
' _ {} ;
