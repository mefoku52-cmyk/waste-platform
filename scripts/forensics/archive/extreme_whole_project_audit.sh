#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"

PHONE_OUTPUT_DIR="/storage/emulated/0/Download"
REPORT_FILE="$PHONE_OUTPUT_DIR/waste-platform-extreme-project-audit-${TIMESTAMP}.txt"

if [[ ! -d "$PHONE_OUTPUT_DIR" ]]; then
    PHONE_OUTPUT_DIR="$HOME/storage/downloads"
    REPORT_FILE="$PHONE_OUTPUT_DIR/waste-platform-extreme-project-audit-${TIMESTAMP}.txt"
fi

if [[ ! -d "$PHONE_OUTPUT_DIR" ]]; then
    echo "ERROR: Android Download storage not available."
    echo "Expected: /storage/emulated/0/Download"
    echo "Fallback: $HOME/storage/downloads"
    exit 1
fi

touch "$REPORT_FILE" 2>/dev/null || {
    echo "ERROR: Cannot write report:"
    echo "$REPORT_FILE"
    exit 1
}

START_EPOCH="$(date +%s)"

export PROJECT_ROOT
export REPORT_FILE

###############################################################################
# HEADER
###############################################################################

cat > "$REPORT_FILE" <<REPORT_HEADER
========================================================================
 WASTE-PLATFORM
 EXTREME WHOLE-PROJECT FORENSIC / STRUCTURAL / LOGICAL AUDIT
========================================================================

PROJECT_ROOT=$PROJECT_ROOT
REPORT_FILE=$REPORT_FILE
TIMESTAMP=$TIMESTAMP

MODE=READ_ONLY
SOURCE_WRITES=NO
RUNTIME_EXECUTION=NO
TEST_EXECUTION=NO
BUILD_EXECUTION=NO
DEPLOYMENT_EXECUTION=NO
DATABASE_EXECUTION=NO
MIGRATION_EXECUTION=NO
PACKAGE_INSTALLATION=NO
SECRET_VALUES=REDACTED

PURPOSE:
  Whole-project structural, logical, provenance and hygiene inventory.

IMPORTANT:
  This audit observes the repository and filesystem.
  It does NOT prove that the application is production-ready.
  It does NOT execute application code.
  It does NOT execute tests.
  It does NOT build.
  It does NOT deploy.
  It does NOT modify source files.

========================================================================
REPORT START
========================================================================

REPORT_HEADER

###############################################################################
# HELPER
###############################################################################

section() {
    {
        echo
        echo "========================================================================"
        echo " $1"
        echo "========================================================================"
    } >> "$REPORT_FILE"
}

line() {
    echo "$1" >> "$REPORT_FILE"
}

safe_count() {
    local value="$1"
    if [[ "$value" =~ ^[0-9]+$ ]]; then
        echo "$value"
    else
        echo "0"
    fi
}

###############################################################################
# BASIC SYSTEM / TOOLING
###############################################################################

section "00. AUDIT ENGINE / ENVIRONMENT"

{
    echo "PWD=$PROJECT_ROOT"
    echo "DATE=$(date)"
    echo "UNAME=$(uname -a 2>/dev/null || true)"
    echo "SHELL=${BASH_VERSION:-unknown}"
    echo "BASH_VERSION=${BASH_VERSION:-unknown}"
    echo "FIND=$(command -v find 2>/dev/null || true)"
    echo "GIT=$(command -v git 2>/dev/null || true)"
    echo "SHA256SUM=$(command -v sha256sum 2>/dev/null || true)"
    echo "PYTHON=$(command -v python3 2>/dev/null || true)"
    echo "NODE=$(command -v node 2>/dev/null || true)"
    echo "NPM=$(command -v npm 2>/dev/null || true)"
    echo "JQ=$(command -v jq 2>/dev/null || true)"
    echo "BC=$(command -v bc 2>/dev/null || true)"
    echo "DU=$(command -v du 2>/dev/null || true)"
    echo "SORT=$(command -v sort 2>/dev/null || true)"
} >> "$REPORT_FILE"

###############################################################################
# PYTHON ENGINE
###############################################################################

section "01. PYTHON WHOLE-PROJECT FORENSIC ENGINE"

python3 - "$REPORT_FILE" "$PROJECT_ROOT" <<'PY'
import os
import sys
import re
import hashlib
import json
import stat
import subprocess
from pathlib import Path
from collections import Counter, defaultdict

REPORT = Path(sys.argv[1])
ROOT = Path(sys.argv[2]).resolve()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_SAMPLE = 50
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024
VERY_LARGE_FILE_THRESHOLD = 100 * 1024 * 1024

TEXT_EXTENSIONS = {
    ".py", ".pyw", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".kts", ".scala", ".groovy",
    ".go", ".rs", ".c", ".h", ".cpp", ".cc", ".hpp",
    ".cs", ".swift", ".m", ".mm",
    ".php", ".rb", ".pl", ".pm",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".xml", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
    ".conf", ".properties", ".env", ".md", ".rst", ".txt",
    ".dockerfile", ".make", ".gradle",
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript/JSX",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/TSX",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin Script",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".php": "PHP",
    ".rb": "Ruby",
    ".pl": "Perl",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".txt": "Text",
    ".env": "Environment",
}

SKIP_HASH_NAMES = {
    ".git",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\/+=]{12,}"),
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"(?i)-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"(?i)github_pat_[A-Za-z0-9_]{20,}"),
]

IMPORT_PATTERNS = {
    "Python": [
        re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", re.M),
        re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import", re.M),
    ],
    "JavaScript": [
        re.compile(r"""(?:import|export).*?from\s*['"]([^'"]+)['"]"""),
        re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "TypeScript": [
        re.compile(r"""(?:import|export).*?from\s*['"]([^'"]+)['"]"""),
        re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "Java": [
        re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", re.M),
    ],
    "Kotlin": [
        re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", re.M),
    ],
    "Go": [
        re.compile(r'^\s*"([^"]+)"', re.M),
    ],
    "Rust": [
        re.compile(r"^\s*(?:use|mod)\s+([A-Za-z0-9_:]+)", re.M),
    ],
}

# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

files = []
dirs = []
symlinks = []
broken_symlinks = []
errors = []

for current, dirnames, filenames in os.walk(ROOT, topdown=True, followlinks=False):
    current_path = Path(current)

    dirs.append(current_path)

    # Do not traverse .git internals as project source.
    dirnames[:] = sorted(
        d for d in dirnames
        if d != ".git"
    )

    for name in sorted(filenames):
        p = current_path / name

        try:
            if p.is_symlink():
                symlinks.append(p)
                if not p.exists():
                    broken_symlinks.append(p)
                continue

            if p.is_file():
                files.append(p)
        except Exception as exc:
            errors.append((str(p), repr(exc)))

# ---------------------------------------------------------------------------
# Basic counts
# ---------------------------------------------------------------------------

ext_counter = Counter()
lang_counter = Counter()
dir_depth_counter = Counter()
file_depth_counter = Counter()
size_total = 0
empty_files = []
large_files = []
very_large_files = []
binary_files = []
text_files = []
zero_byte_files = []

line_count_total = 0
line_count_by_language = Counter()

todo_hits = []
fixme_hits = []
xxx_hits = []
hack_hits = []
placeholder_hits = []

secret_hits = []

permissions_world_writable = []
permissions_executable = []

hash_groups = defaultdict(list)
name_groups = defaultdict(list)

manifest_files = []
config_files = []
env_files = []
test_files = []
documentation_files = []
ci_files = []
deployment_files = []
database_files = []
docker_files = []
entrypoint_candidates = []

logical_edges = []
import_counter = Counter()
referenced_local_candidates = Counter()

def rel(p):
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)

def is_probably_text(data):
    if not data:
        return True
    if b"\x00" in data[:8192]:
        return False
    return True

def language_for(p):
    ext = p.suffix.lower()
    if ext in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext]
    if p.name.lower() in {"dockerfile", "makefile", "justfile"}:
        return p.name
    return "Other"

def safe_read(p, limit=2*1024*1024):
    try:
        with p.open("rb") as f:
            return f.read(limit)
    except Exception:
        return b""

# ---------------------------------------------------------------------------
# File inventory
# ---------------------------------------------------------------------------

for p in files:
    try:
        st = p.stat()
        size = st.st_size
        size_total += size

        ext = p.suffix.lower() if p.suffix else "[no_extension]"
        ext_counter[ext] += 1

        lang = language_for(p)
        lang_counter[lang] += 1

        depth = len(p.relative_to(ROOT).parts) - 1
        file_depth_counter[depth] += 1

        if size == 0:
            zero_byte_files.append(p)

        if size > LARGE_FILE_THRESHOLD:
            large_files.append((p, size))

        if size > VERY_LARGE_FILE_THRESHOLD:
            very_large_files.append((p, size))

        mode = stat.S_IMODE(st.st_mode)

        if mode & stat.S_IWOTH:
            permissions_world_writable.append((p, oct(mode)))

        if mode & stat.S_IXUSR:
            permissions_executable.append((p, oct(mode)))

        name_lower = p.name.lower()
        path_lower = rel(p).lower()

        name_groups[name_lower].append(p)

        if (
            name_lower in {
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "requirements.txt",
                "pyproject.toml",
                "poetry.lock",
                "pipfile",
                "pipfile.lock",
                "cargo.toml",
                "cargo.lock",
                "go.mod",
                "go.sum",
                "build.gradle",
                "build.gradle.kts",
                "settings.gradle",
                "settings.gradle.kts",
                "gradle.properties",
                "pom.xml",
                "composer.json",
                "gemfile",
                "gemfile.lock",
                "mix.exs",
                "pubspec.yaml",
            }
            or "requirements" in name_lower
        ):
            manifest_files.append(p)

        if (
            name_lower.startswith(".env")
            or ".env." in name_lower
        ):
            env_files.append(p)

        if (
            ".github/workflows/" in path_lower
            or name_lower in {"jenkinsfile", ".gitlab-ci.yml", "bitbucket-pipelines.yml"}
        ):
            ci_files.append(p)

        if (
            name_lower in {
                "deploy.sh",
                "release.sh",
                "dockerfile",
                "docker-compose.yml",
                "docker-compose.yaml",
            }
            or "deploy" in name_lower
            or "release" in name_lower
        ):
            deployment_files.append(p)

        if (
            p.suffix.lower() == ".sql"
            or "migration" in path_lower
            or "alembic" in path_lower
            or "schema" in name_lower
        ):
            database_files.append(p)

        if (
            name_lower == "dockerfile"
            or "docker-compose" in name_lower
            or name_lower.endswith(".dockerfile")
        ):
            docker_files.append(p)

        if (
            "test" in path_lower
            or name_lower.startswith("test_")
            or name_lower.endswith("_test.py")
            or name_lower.endswith(".test.js")
            or name_lower.endswith(".spec.js")
            or name_lower.endswith(".spec.ts")
        ):
            test_files.append(p)

        if (
            p.suffix.lower() in {".md", ".rst", ".txt"}
            or name_lower in {"readme", "readme.md", "changelog.md", "contributing.md"}
        ):
            documentation_files.append(p)

        if (
            name_lower in {
                "main.py",
                "app.py",
                "server.py",
                "manage.py",
                "main.js",
                "index.js",
                "server.js",
                "main.ts",
                "index.ts",
                "main.kt",
                "application.kt",
                "main.go",
                "main.rs",
                "start.sh",
                "run.sh",
                "start-platform.sh",
            }
        ):
            entrypoint_candidates.append(p)

        if size <= 5 * 1024 * 1024:
            data = safe_read(p)

            if is_probably_text(data):
                text_files.append(p)

                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = ""

                lines = text.count("\n") + (1 if text else 0)
                line_count_total += lines
                line_count_by_language[lang] += lines

                for idx, rawline in enumerate(text.splitlines(), 1):
                    stripped = rawline.strip()

                    if re.search(r"(?i)\bTODO\b", rawline):
                        todo_hits.append((p, idx, stripped[:240]))

                    if re.search(r"(?i)\bFIXME\b", rawline):
                        fixme_hits.append((p, idx, stripped[:240]))

                    if re.search(r"(?i)\bXXX\b", rawline):
                        xxx_hits.append((p, idx, stripped[:240]))

                    if re.search(r"(?i)\bHACK\b", rawline):
                        hack_hits.append((p, idx, stripped[:240]))

                    if re.search(r"(?i)\b(?:placeholder|not implemented|implement me)\b", rawline):
                        placeholder_hits.append((p, idx, stripped[:240]))

                    for pat in SECRET_PATTERNS:
                        if pat.search(rawline):
                            secret_hits.append(
                                (p, idx, pat.pattern[:80])
                            )
                            break

                # Hash text and binary alike where size permits.
                try:
                    digest = hashlib.sha256(p.read_bytes()).hexdigest()
                    hash_groups[digest].append(p)
                except Exception:
                    pass
            else:
                binary_files.append(p)

        else:
            # Large files are hashed without loading into memory.
            try:
                h = hashlib.sha256()
                with p.open("rb") as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        h.update(chunk)
                hash_groups[h.hexdigest()].append(p)
            except Exception:
                pass

    except Exception as exc:
        errors.append((str(p), repr(exc)))

# ---------------------------------------------------------------------------
# Directory depths
# ---------------------------------------------------------------------------

for d in dirs:
    try:
        depth = len(d.relative_to(ROOT).parts)
        dir_depth_counter[depth] += 1
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Duplicate groups
# ---------------------------------------------------------------------------

duplicate_hash_groups = {
    h: ps for h, ps in hash_groups.items()
    if len(ps) > 1
}

duplicate_name_groups = {
    n: ps for n, ps in name_groups.items()
    if len(ps) > 1
}

# ---------------------------------------------------------------------------
# Logical source connection analysis
# ---------------------------------------------------------------------------

def candidate_local_paths(source, token):
    result = []

    if not token:
        return result

    token = token.strip()

    if token.startswith("."):
        base = source.parent

        candidates = [
            base / token,
            base / (token + ".py"),
            base / (token + ".js"),
            base / (token + ".ts"),
            base / (token + ".tsx"),
            base / (token + ".jsx"),
            base / (token + ".json"),
            base / (token + ".kt"),
            base / (token + ".kts"),
            base / (token + ".go"),
            base / (token + ".rs"),
            base / (token + ".sh"),
            base / token / "index.js",
            base / token / "index.ts",
            base / token / "index.tsx",
            base / token / "__init__.py",
        ]

        for c in candidates:
            try:
                if c.exists() and c.is_file():
                    result.append(c.resolve())
            except Exception:
                pass

    return result

for p in text_files:
    lang = language_for(p)

    patterns = IMPORT_PATTERNS.get(lang, [])

    if not patterns:
        continue

    try:
        if p.stat().st_size > 2 * 1024 * 1024:
            continue

        text = p.read_text(errors="replace")

        tokens = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                if match.groups():
                    tokens.append(match.group(1))

        for token in tokens:
            import_counter[token] += 1

            for target in candidate_local_paths(p, token):
                logical_edges.append((p, target, token))
                referenced_local_candidates[target] += 1

    except Exception:
        continue

# ---------------------------------------------------------------------------
# Potential orphan source files
# ---------------------------------------------------------------------------

source_files = [
    p for p in files
    if language_for(p) in {
        "Python", "JavaScript", "TypeScript", "Java",
        "Kotlin", "Kotlin Script", "Go", "Rust",
        "C", "C++", "C/C++ Header", "C++ Header",
        "C#", "Swift", "PHP", "Ruby", "Perl", "Shell"
    }
]

referenced_targets = set(referenced_local_candidates)

orphan_candidates = []

for p in source_files:
    name = p.name
    if name.lower() in {
        "__init__.py",
        "index.js",
        "index.ts",
        "index.tsx",
        "main.py",
        "main.js",
        "main.ts",
        "main.go",
        "main.rs",
        "app.py",
        "server.py",
    }:
        continue

    if p not in referenced_targets:
        orphan_candidates.append(p)

# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def git_cmd(*args):
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as exc:
        return 99, "", repr(exc)

git_available = False
git_branch = ""
git_branches = []
git_status = []
git_tracked = []
git_untracked = []
git_modified = []
git_deleted = []

code, out, err = git_cmd("rev-parse", "--is-inside-work-tree")
if code == 0 and out.strip() == "true":
    git_available = True

if git_available:
    _, out, _ = git_cmd("branch", "--show-current")
    git_branch = out.strip()

    _, out, _ = git_cmd("branch", "--format=%(refname:short)")
    git_branches = [x.strip() for x in out.splitlines() if x.strip()]

    _, out, _ = git_cmd("status", "--short")
    git_status = [x for x in out.splitlines() if x.strip()]

    _, out, _ = git_cmd("ls-files")
    git_tracked = [x for x in out.splitlines() if x.strip()]

    for item in git_status:
        codepart = item[:2]
        pathpart = item[3:].strip()

        if "??" in codepart:
            git_untracked.append(pathpart)

        if "M" in codepart:
            git_modified.append(pathpart)

        if "D" in codepart:
            git_deleted.append(pathpart)

# ---------------------------------------------------------------------------
# Write structured report
# ---------------------------------------------------------------------------

def write(title, lines):
    REPORT.write_text(
        REPORT.read_text(errors="replace") + "\n" +
        "=" * 72 + "\n" +
        " " + title + "\n" +
        "=" * 72 + "\n" +
        "\n".join(str(x) for x in lines) +
        "\n"
    )

def append(title, lines):
    with REPORT.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 72 + "\n")
        f.write(" " + title + "\n")
        f.write("=" * 72 + "\n")
        for x in lines:
            f.write(str(x) + "\n")

# ---------------------------------------------------------------------------
# 02 GLOBAL COUNTS
# ---------------------------------------------------------------------------

append("02. GLOBAL PROJECT COUNTS", [
    f"TOTAL_DIRECTORIES={len(dirs)}",
    f"TOTAL_FILES={len(files)}",
    f"TOTAL_SYMLINKS={len(symlinks)}",
    f"BROKEN_SYMLINKS={len(broken_symlinks)}",
    f"TOTAL_SIZE_BYTES={size_total}",
    f"TOTAL_SIZE_MB={size_total / 1024 / 1024:.2f}",
    f"TOTAL_ESTIMATED_LINES={line_count_total}",
    f"TEXT_FILES={len(text_files)}",
    f"BINARY_FILES={len(binary_files)}",
    f"ZERO_BYTE_FILES={len(zero_byte_files)}",
    f"LARGE_FILES_GT_10MB={len(large_files)}",
    f"VERY_LARGE_FILES_GT_100MB={len(very_large_files)}",
    f"WORLD_WRITABLE_FILES={len(permissions_world_writable)}",
    f"EXECUTABLE_FILES={len(permissions_executable)}",
    f"READ_ERRORS={len(errors)}",
])

# ---------------------------------------------------------------------------
# 03 DEPTH
# ---------------------------------------------------------------------------

append("03. DIRECTORY / FILE DEPTH", [
    "DIRECTORY_DEPTH_DISTRIBUTION:",
    *[
        f"  DEPTH_{k}={v}"
        for k, v in sorted(dir_depth_counter.items())
    ],
    "FILE_DEPTH_DISTRIBUTION:",
    *[
        f"  DEPTH_{k}={v}"
        for k, v in sorted(file_depth_counter.items())
    ],
    f"MAX_DIRECTORY_DEPTH={max(dir_depth_counter) if dir_depth_counter else 0}",
    f"MAX_FILE_DEPTH={max(file_depth_counter) if file_depth_counter else 0}",
])

# ---------------------------------------------------------------------------
# 04 EXTENSIONS / LANGUAGES
# ---------------------------------------------------------------------------

append("04. FILE TYPES / LANGUAGES", [
    "LANGUAGE_COUNTS:",
    *[
        f"  {k}={v}"
        for k, v in lang_counter.most_common()
    ],
    "",
    "EXTENSION_COUNTS:",
    *[
        f"  {k}={v}"
        for k, v in ext_counter.most_common()
    ],
])

# ---------------------------------------------------------------------------
# 05 SIZE OUTLIERS
# ---------------------------------------------------------------------------

append("05. SIZE OUTLIERS", [
    f"LARGE_FILE_THRESHOLD_BYTES={LARGE_FILE_THRESHOLD}",
    f"VERY_LARGE_FILE_THRESHOLD_BYTES={VERY_LARGE_FILE_THRESHOLD}",
    "VERY_LARGE_FILES:",
    *[
        f"  {rel(p)} :: {size} bytes :: {size / 1024 / 1024:.2f} MB"
        for p, size in sorted(very_large_files, key=lambda x: x[1], reverse=True)[:100]
    ],
    "LARGE_FILES:",
    *[
        f"  {rel(p)} :: {size} bytes :: {size / 1024 / 1024:.2f} MB"
        for p, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:100]
    ],
])

# ---------------------------------------------------------------------------
# 06 DUPLICATES
# ---------------------------------------------------------------------------

append("06. DUPLICATE FILE CONTENT / SHA-256", [
    f"DUPLICATE_CONTENT_GROUPS={len(duplicate_hash_groups)}",
    f"DUPLICATE_CONTENT_FILES={sum(len(v) for v in duplicate_hash_groups.values())}",
    "",
    "DUPLICATE_GROUPS:",
    *[
        (
            f"  HASH={h}\n" +
            "\n".join(f"    {rel(p)}" for p in ps)
        )
        for h, ps in sorted(
            duplicate_hash_groups.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:200]
    ],
])

append("07. DUPLICATE BASENAME ANALYSIS", [
    f"DUPLICATE_BASENAME_GROUPS={len(duplicate_name_groups)}",
    f"DUPLICATE_BASENAME_FILES={sum(len(v) for v in duplicate_name_groups.values())}",
    "DUPLICATE_BASENAMES:",
    *[
        (
            f"  NAME={name}\n" +
            "\n".join(f"    {rel(p)}" for p in ps)
        )
        for name, ps in sorted(
            duplicate_name_groups.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:200]
    ],
])

# ---------------------------------------------------------------------------
# 08 SYMLINKS
# ---------------------------------------------------------------------------

append("08. SYMLINKS / BROKEN LINKS", [
    f"SYMLINK_COUNT={len(symlinks)}",
    f"BROKEN_SYMLINK_COUNT={len(broken_symlinks)}",
    "SYMLINKS:",
    *[f"  {rel(p)} -> {os.readlink(p)}" for p in symlinks[:200]],
    "BROKEN_SYMLINKS:",
    *[f"  {rel(p)}" for p in broken_symlinks[:200]],
])

# ---------------------------------------------------------------------------
# 09 PERMISSIONS
# ---------------------------------------------------------------------------

append("09. FILE PERMISSIONS", [
    f"WORLD_WRITABLE_COUNT={len(permissions_world_writable)}",
    "WORLD_WRITABLE_FILES:",
    *[
        f"  {rel(p)} :: MODE={mode}"
        for p, mode in permissions_world_writable[:200]
    ],
    f"EXECUTABLE_FILE_COUNT={len(permissions_executable)}",
])

# ---------------------------------------------------------------------------
# 10 TODO / TECHNICAL DEBT
# ---------------------------------------------------------------------------

append("10. TODO / FIXME / HACK / PLACEHOLDER INVENTORY", [
    f"TODO_COUNT={len(todo_hits)}",
    f"FIXME_COUNT={len(fixme_hits)}",
    f"XXX_COUNT={len(xxx_hits)}",
    f"HACK_COUNT={len(hack_hits)}",
    f"PLACEHOLDER_COUNT={len(placeholder_hits)}",
    "",
    "TODO:",
    *[f"  {rel(p)}:{n}: {text}" for p,n,text in todo_hits[:300]],
    "",
    "FIXME:",
    *[f"  {rel(p)}:{n}: {text}" for p,n,text in fixme_hits[:300]],
    "",
    "PLACEHOLDER / NOT IMPLEMENTED:",
    *[f"  {rel(p)}:{n}: {text}" for p,n,text in placeholder_hits[:300]],
])

# ---------------------------------------------------------------------------
# 11 SECRET PATTERNS
# ---------------------------------------------------------------------------

append("11. SECRET-LIKE PATTERN INVENTORY", [
    f"SECRET_LIKE_MATCH_COUNT={len(secret_hits)}",
    "IMPORTANT: VALUES ARE NEVER PRINTED.",
    "MATCHES:",
    *[
        f"  {rel(p)}:{n} :: PATTERN={pattern}"
        for p,n,pattern in secret_hits[:300]
    ],
])

# ---------------------------------------------------------------------------
# 12 CONFIG / ENV / MANIFEST
# ---------------------------------------------------------------------------

append("12. CONFIGURATION / ENVIRONMENT / DEPENDENCY SURFACE", [
    f"ENV_FILE_COUNT={len(env_files)}",
    "ENV_FILES:",
    *[f"  {rel(p)}" for p in env_files[:300]],
    "",
    f"MANIFEST_COUNT={len(manifest_files)}",
    "MANIFEST_FILES:",
    *[f"  {rel(p)}" for p in manifest_files[:300]],
    "",
    f"CONFIG_FILE_COUNT={len(config_files)}",
])

# ---------------------------------------------------------------------------
# 13 TESTS
# ---------------------------------------------------------------------------

append("13. TEST SURFACE", [
    f"TEST_FILE_COUNT={len(test_files)}",
    "TEST_FILES:",
    *[f"  {rel(p)}" for p in test_files[:500]],
])

# ---------------------------------------------------------------------------
# 14 DOCUMENTATION
# ---------------------------------------------------------------------------

append("14. DOCUMENTATION SURFACE", [
    f"DOCUMENTATION_FILE_COUNT={len(documentation_files)}",
    "DOCUMENTATION_FILES:",
    *[f"  {rel(p)}" for p in documentation_files[:500]],
])

# ---------------------------------------------------------------------------
# 15 CI / DEPLOYMENT / DOCKER
# ---------------------------------------------------------------------------

append("15. CI / CD / DEPLOYMENT SURFACE", [
    f"CI_FILE_COUNT={len(ci_files)}",
    "CI_FILES:",
    *[f"  {rel(p)}" for p in ci_files[:300]],
    "",
    f"DEPLOYMENT_CANDIDATE_COUNT={len(deployment_files)}",
    "DEPLOYMENT_CANDIDATES:",
    *[f"  {rel(p)}" for p in deployment_files[:300]],
    "",
    f"DOCKER_FILE_COUNT={len(docker_files)}",
    "DOCKER_FILES:",
    *[f"  {rel(p)}" for p in docker_files[:200]],
])

# ---------------------------------------------------------------------------
# 16 DATABASE
# ---------------------------------------------------------------------------

append("16. DATABASE / MIGRATION / SCHEMA SURFACE", [
    f"DATABASE_ARTIFACT_COUNT={len(database_files)}",
    "DATABASE_ARTIFACTS:",
    *[f"  {rel(p)}" for p in database_files[:500]],
])

# ---------------------------------------------------------------------------
# 17 ENTRYPOINTS
# ---------------------------------------------------------------------------

append("17. ENTRYPOINT CANDIDATES", [
    f"ENTRYPOINT_CANDIDATE_COUNT={len(entrypoint_candidates)}",
    "ENTRYPOINT_CANDIDATES:",
    *[f"  {rel(p)}" for p in entrypoint_candidates[:300]],
])

# ---------------------------------------------------------------------------
# 18 LOGICAL CONNECTIONS
# ---------------------------------------------------------------------------

append("18. LOGICAL SOURCE CONNECTIONS", [
    f"LOGICAL_IMPORT_TOKENS={sum(import_counter.values())}",
    f"LOCAL_LOGICAL_EDGES={len(logical_edges)}",
    f"REFERENCED_LOCAL_TARGETS={len(referenced_targets)}",
    "",
    "MOST_FREQUENT_IMPORT TOKENS:",
    *[
        f"  {token} :: {count}"
        for token,count in import_counter.most_common(100)
    ],
    "",
    "LOCAL SOURCE EDGES:",
    *[
        f"  {rel(src)} -> {rel(dst)} :: token={token}"
        for src,dst,token in logical_edges[:1000]
    ],
])

# ---------------------------------------------------------------------------
# 19 ORPHAN CANDIDATES
# ---------------------------------------------------------------------------

append("19. POTENTIAL ORPHAN SOURCE FILES", [
    "NOTE: These are candidates only, not proof of dead code.",
    f"POTENTIAL_ORPHAN_SOURCE_COUNT={len(orphan_candidates)}",
    "POTENTIAL_ORPHANS:",
    *[f"  {rel(p)}" for p in orphan_candidates[:500]],
])

# ---------------------------------------------------------------------------
# 20 LINE COUNTS
# ---------------------------------------------------------------------------

append("20. SOURCE SIZE / LINE COUNTS", [
    f"TOTAL_ESTIMATED_LINES={line_count_total}",
    "LINES_BY_LANGUAGE:",
    *[
        f"  {k}={v}"
        for k,v in line_count_by_language.most_common()
    ],
])

# ---------------------------------------------------------------------------
# 21 GIT
# ---------------------------------------------------------------------------

append("21. GIT REPOSITORY STATE", [
    f"GIT_REPOSITORY_PRESENT={git_available}",
    f"CURRENT_BRANCH={git_branch}",
    f"BRANCH_COUNT={len(git_branches)}",
    "BRANCHES:",
    *[f"  {b}" for b in git_branches],
    "",
    f"TRACKED_FILE_COUNT={len(git_tracked)}",
    f"STATUS_ENTRY_COUNT={len(git_status)}",
    f"UNTRACKED_COUNT={len(git_untracked)}",
    f"MODIFIED_COUNT={len(git_modified)}",
    f"DELETED_COUNT={len(git_deleted)}",
    "",
    "GIT_STATUS:",
    *[f"  {x}" for x in git_status[:1000]],
])

# ---------------------------------------------------------------------------
# 22 PROJECT TOPOLOGY
# ---------------------------------------------------------------------------

top_level = sorted({
    rel(p).split(os.sep)[0]
    for p in dirs + files
    if rel(p) != "."
})

append("22. PROJECT TOPOLOGY", [
    f"TOP_LEVEL_NODE_COUNT={len(top_level)}",
    "TOP_LEVEL_NODES:",
    *[f"  {x}" for x in top_level],
    "",
    "TOP_DIRECTORIES_BY_FILE_COUNT:",
    *[
        f"  {rel(d)}"
        for d in sorted(
            dirs,
            key=lambda d: sum(
                1 for p in files
                if str(p).startswith(str(d) + os.sep)
            ),
            reverse=True
        )[:100]
    ],
])

# ---------------------------------------------------------------------------
# 23 RISK INDICATORS
# ---------------------------------------------------------------------------

risk_score = 0

if broken_symlinks:
    risk_score += min(10, len(broken_symlinks))

if duplicate_hash_groups:
    risk_score += min(10, len(duplicate_hash_groups))

if permissions_world_writable:
    risk_score += min(10, len(permissions_world_writable))

if secret_hits:
    risk_score += min(20, len(secret_hits))

if placeholder_hits:
    risk_score += min(10, len(placeholder_hits))

if fixme_hits:
    risk_score += min(10, len(fixme_hits))

if very_large_files:
    risk_score += min(10, len(very_large_files))

if git_status:
    risk_score += min(10, len(git_status))

append("23. NON-BINDING STRUCTURAL RISK INDICATORS", [
    f"STRUCTURAL_RISK_INDICATOR_SCORE={risk_score}",
    "",
    "This score is NOT a security score.",
    "This score is NOT a production-readiness score.",
    "It is only a triage indicator for findings requiring inspection.",
    "",
    f"BROKEN_SYMLINKS={len(broken_symlinks)}",
    f"DUPLICATE_CONTENT_GROUPS={len(duplicate_hash_groups)}",
    f"WORLD_WRITABLE_FILES={len(permissions_world_writable)}",
    f"SECRET_LIKE_MATCHES={len(secret_hits)}",
    f"PLACEHOLDER_MATCHES={len(placeholder_hits)}",
    f"FIXME_MATCHES={len(fixme_hits)}",
    f"VERY_LARGE_FILES={len(very_large_files)}",
    f"GIT_STATUS_ENTRIES={len(git_status)}",
])

# ---------------------------------------------------------------------------
# 24 FILE INVENTORY
# ---------------------------------------------------------------------------

append("24. COMPLETE RECURSIVE FILE INVENTORY", [
    f"FILES={len(files)}",
    "PATH | SIZE_BYTES | SHA256",
    *[
        (
            f"{rel(p)} | "
            f"{p.stat().st_size if p.exists() else 0} | "
            f"{next((h for h,ps in hash_groups.items() if p in ps), 'UNHASHED')}"
        )
        for p in sorted(files)
    ],
])

# ---------------------------------------------------------------------------
# 25 DIRECTORY INVENTORY
# ---------------------------------------------------------------------------

append("25. COMPLETE RECURSIVE DIRECTORY INVENTORY", [
    f"DIRECTORIES={len(dirs)}",
    *[f"{rel(d)}" for d in sorted(dirs)],
])

# ---------------------------------------------------------------------------
# 26 FINAL INTERNAL COUNTS
# ---------------------------------------------------------------------------

append("26. FINAL AUDIT COUNTERS", [
    f"FILES={len(files)}",
    f"DIRECTORIES={len(dirs)}",
    f"SYMLINKS={len(symlinks)}",
    f"BROKEN_SYMLINKS={len(broken_symlinks)}",
    f"DUPLICATE_CONTENT_GROUPS={len(duplicate_hash_groups)}",
    f"DUPLICATE_BASENAME_GROUPS={len(duplicate_name_groups)}",
    f"TEST_FILES={len(test_files)}",
    f"DOCUMENTATION_FILES={len(documentation_files)}",
    f"ENV_FILES={len(env_files)}",
    f"MANIFEST_FILES={len(manifest_files)}",
    f"CI_FILES={len(ci_files)}",
    f"DEPLOYMENT_CANDIDATES={len(deployment_files)}",
    f"DATABASE_ARTIFACTS={len(database_files)}",
    f"DOCKER_FILES={len(docker_files)}",
    f"ENTRYPOINT_CANDIDATES={len(entrypoint_candidates)}",
    f"TODO={len(todo_hits)}",
    f"FIXME={len(fixme_hits)}",
    f"HACK={len(hack_hits)}",
    f"PLACEHOLDER={len(placeholder_hits)}",
    f"SECRET_LIKE_MATCHES={len(secret_hits)}",
    f"LOCAL_LOGICAL_EDGES={len(logical_edges)}",
    f"POTENTIAL_ORPHANS={len(orphan_candidates)}",
    f"GIT_BRANCHES={len(git_branches)}",
    f"GIT_STATUS_ENTRIES={len(git_status)}",
    f"READ_ERRORS={len(errors)}",
])

if errors:
    append("27. READ ERRORS", [
        f"ERROR_COUNT={len(errors)}",
        *[
            f"  {p} :: {e}"
            for p,e in errors[:500]
        ],
    ])

append("28. AUDIT LIMITATIONS / INTERPRETATION", [
    "1. Duplicate SHA-256 means byte-identical content, not necessarily duplicate purpose.",
    "2. Duplicate basenames are not automatically a defect.",
    "3. Potential orphan files require architectural/contextual verification.",
    "4. Import analysis is heuristic and language-specific.",
    "5. Secret-like matches are patterns only and values are intentionally redacted.",
    "6. CI/CD detection is heuristic and does not prove deployment authority.",
    "7. No runtime behavior was executed.",
    "8. No test suite was executed.",
    "9. No build was executed.",
    "10. No deployment was executed.",
    "11. No source files were modified by this audit engine.",
    "12. Historical audit scripts remain part of the filesystem inventory.",
    "13. .git internals are intentionally excluded from recursive source traversal.",
])

PY

###############################################################################
# SHELL-LEVEL GIT DETAILS
###############################################################################

section "29. GIT STRUCTURAL SUMMARY"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    {
        echo "GIT_STATUS_PORCELAIN:"
        git status --porcelain 2>/dev/null || true
        echo
        echo "GIT_BRANCHES:"
        git branch -a 2>/dev/null || true
        echo
        echo "GIT_LAST_COMMITS:"
        git log --oneline --decorate -20 2>/dev/null || true
        echo
        echo "GIT_REMOTES:"
        git remote -v 2>/dev/null || true
    } >> "$REPORT_FILE"
else
    echo "GIT_REPOSITORY=NO" >> "$REPORT_FILE"
fi

###############################################################################
# FINAL SHELL INVENTORY
###############################################################################

section "30. SHELL / SCRIPT LANGUAGE INVENTORY"

{
    echo "SHELL_SCRIPT_FILES:"
    find . -type f \
        \( -name "*.sh" -o -name "*.bash" -o -name "*.zsh" -o -name "*.fish" \) \
        -not -path "./.git/*" \
        -print 2>/dev/null | sort

    echo
    echo "EXECUTABLE_FILES:"
    find . -type f -perm -111 \
        -not -path "./.git/*" \
        -print 2>/dev/null | sort
} >> "$REPORT_FILE"

###############################################################################
# FILE NAME / PATH ANOMALIES
###############################################################################

section "31. PATH / NAME ANOMALIES"

{
    echo "FILES_WITH_SPACES:"
    find . -type f -not -path "./.git/*" \
        -name "* *" -print 2>/dev/null | sort

    echo
    echo "FILES_WITH_TABS:"
    find . -type f -not -path "./.git/*" \
        -print0 2>/dev/null |
        while IFS= read -r -d '' f; do
            if [[ "$f" == *$'\t'* ]]; then
                echo "$f"
            fi
        done

    echo
    echo "HIDDEN_FILES_COUNT:"
    find . -type f -name ".*" -not -path "./.git/*" \
        -print 2>/dev/null | wc -l

    echo
    echo "HIDDEN_DIRECTORIES_COUNT:"
    find . -type d -name ".*" -not -path "./.git/*" \
        -print 2>/dev/null | wc -l
} >> "$REPORT_FILE"

###############################################################################
# COMMON ARCHIVE / GENERATED / CACHE SURFACE
###############################################################################

section "32. GENERATED / CACHE / BUILD ARTIFACT SURFACE"

{
    echo "NODE_MODULES_DIRECTORIES:"
    find . -type d -name "node_modules" \
        -not -path "./.git/*" \
        -print 2>/dev/null | sort

    echo
    echo "PYTHON_CACHE_DIRECTORIES:"
    find . -type d \
        \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" \) \
        -not -path "./.git/*" \
        -print 2>/dev/null | sort

    echo
    echo "BUILD_DIRECTORIES:"
    find . -type d \
        \( -name "build" -o -name "dist" -o -name "target" -o -name ".gradle" -o -name ".next" -o -name "out" \) \
        -not -path "./.git/*" \
        -print 2>/dev/null | sort

    echo
    echo "ARCHIVE_FILES:"
    find . -type f \
        \( -name "*.zip" -o -name "*.tar" -o -name "*.tar.gz" -o -name "*.tgz" -o -name "*.7z" -o -name "*.rar" \) \
        -not -path "./.git/*" \
        -print 2>/dev/null | sort
} >> "$REPORT_FILE"

###############################################################################
# FINAL SAFETY / COMPLETION
###############################################################################

END_EPOCH="$(date +%s)"
ELAPSED="$((END_EPOCH - START_EPOCH))"

section "33. FINAL AUDIT STATUS"

{
    echo "AUDIT_COMPLETE=YES"
    echo "AUDIT_EXIT_CODE=0"
    echo "READ_ONLY=YES"
    echo "SOURCE_WRITES=NO"
    echo "RUNTIME_EXECUTION=NO"
    echo "TEST_EXECUTION=NO"
    echo "BUILD_EXECUTION=NO"
    echo "DEPLOYMENT_EXECUTION=NO"
    echo "DATABASE_EXECUTION=NO"
    echo "MIGRATION_EXECUTION=NO"
    echo "PACKAGE_INSTALLATION=NO"
    echo "PROJECT_MODIFICATION=NO"
    echo "REPORT_WRITE_ONLY=YES"
    echo "ELAPSED_SECONDS=$ELAPSED"
    echo "REPORT_SIZE_BYTES=$(wc -c < "$REPORT_FILE" 2>/dev/null || echo 0)"
    echo
    echo "REPORT_PATH=$REPORT_FILE"
    echo
    echo "NEXT_ACTION:"
    echo "  Send the COMPLETE REPORT_FILE content for analysis."
    echo
    echo "IMPORTANT:"
    echo "  Do not manually edit the report before sending it."
    echo "  The report is intended to be analyzed as one complete artifact."
} >> "$REPORT_FILE"

echo
echo "============================================================"
echo " EXTREME WHOLE-PROJECT AUDIT COMPLETE"
echo "============================================================"
echo "AUDIT_COMPLETE=YES"
echo "READ_ONLY=YES"
echo "SOURCE_WRITES=NO"
echo "RUNTIME_EXECUTION=NO"
echo "TEST_EXECUTION=NO"
echo "BUILD_EXECUTION=NO"
echo "DEPLOYMENT_EXECUTION=NO"
echo "DATABASE_EXECUTION=NO"
echo "MIGRATION_EXECUTION=NO"
echo "PACKAGE_INSTALLATION=NO"
echo
echo "REPORT=$REPORT_FILE"
echo "SIZE=$(wc -c < "$REPORT_FILE" 2>/dev/null || echo 0) bytes"
echo
echo "POSLI COMPLETE REPORT:"
echo "$REPORT_FILE"
echo "============================================================"

exit 0
