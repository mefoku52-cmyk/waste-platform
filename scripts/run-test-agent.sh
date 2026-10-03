#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

PROMPT='You are working in the waste-platform repository.

HARD RULES:
- Do not delete any file or directory.
- Do not modify application/production source outside tests/.
- Do not fix product bugs. Record them only.
- Do not run git commit, git push, git reset, git checkout --, git clean, or git rebase.
- Read product code. Write only under tests/unit/ and tests/integration/.
- Leave correct existing tests unchanged.
- If a test fails because product code is wrong, do not patch the product.
- If a test fails because the test is wrong, you may edit only that test file.
- Never stop after the first failure.
- Do not ask for confirmation. Work until the report is ready.

GOAL:
Complete and run the test suite. Many tests already exist. Discover coverage, then add missing high-value tests.

HOW:
1. Inspect repo layout, existing tests, and pytest config.
2. Read real service/API code before writing assertions.
3. Add tests only under tests/. Match existing style.
4. Run without fail-fast:
   python -m pytest tests/ -v --tb=short --maxfail=0
   If the repo documents another runner, use that instead, still without fail-fast.
5. If a test needs product-code changes, mark it BLOCKED.

FINAL REPORT in English:
- commands run
- collected / passed / failed / skipped / errors
- new test files
- test files edited and why
- failures: file, name, short reason
- product bugs noticed but NOT fixed
- blocked items
- confirmation: no product source changed, no deletes, no commits

Start now.'

pick_agent() {
  if command -v claude >/dev/null 2>&1; then
    echo claude
    return
  fi
  if command -v aider >/dev/null 2>&1; then
    echo aider
    return
  fi
  if command -v opencode >/dev/null 2>&1; then
    echo opencode
    return
  fi
  if command -v codex >/dev/null 2>&1; then
    echo codex
    return
  fi
  if command -v gemini >/dev/null 2>&1; then
    echo gemini
    return
  fi
  echo ""
}

AGENT="$(pick_agent)"
if [ -z "$AGENT" ]; then
  echo "No AI CLI found (claude, aider, opencode, codex, gemini)."
  echo "Install one of them, then run: bash \~/waste-platform/scripts/run-test-agent.sh"
  exit 1
fi

echo "Starting $AGENT in $PWD"
echo "Rules: tests only, no product edits, no delete, no commit."

case "$AGENT" in
  claude)
    exec claude "$PROMPT"
    ;;
  aider)
    exec aider --yes-always --no-auto-commits --message "$PROMPT"
    ;;
  opencode)
    exec opencode run "$PROMPT"
    ;;
  codex)
    exec codex "$PROMPT"
    ;;
  gemini)
    exec gemini -p "$PROMPT"
    ;;
esac
