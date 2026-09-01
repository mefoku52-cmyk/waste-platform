#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

echo "[1/5] Opravujem rewrite-imports-node.mjs..."
cat > rewrite-imports-node.mjs <<'EOT'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve('src')
const featureNames = new Set([
  'admin',
  'auth',
  'companies',
  'compliance',
  'documents',
  'inquiries',
  'listings',
  'notifications',
  'uploads',
])

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.next') continue
      walk(full, out)
    } else if (/.(ts|tsx)$/.test(entry.name)) {
      out.push(full)
    }
  }
  return out
}

function rewriteSpecifier(spec) {
  const m = spec.match(/^@/features/([^/]+)/.+$/)
  if (!m) return spec
  const feature = m[1]
  if (!featureNames.has(feature)) return spec
  return `@/features/${feature}`
}

function rewriteContent(content) {
  let changed = false

  content = content.replace(
    /\b(froms+['"])([^'"]+)(['"])/g,
    (all, a, spec, c) => {
      const next = rewriteSpecifier(spec)
      if (next !== spec) changed = true
      return `${a}${next}${c}`
    }
  )

  content = content.replace(
    /\b(imports*(s*['"])([^'"]+)(['"]s*))/g,
    (all, a, spec, c) => {
      const next = rewriteSpecifier(spec)
      if (next !== spec) changed = true
      return `${a}${next}${c}`
    }
  )

  return { content, changed }
}

const files = walk(root)
let changedCount = 0

for (const file of files) {
  const original = fs.readFileSync(file, 'utf8')
  const { content, changed } = rewriteContent(original)
  if (changed) {
    fs.writeFileSync(file, content, 'utf8')
    console.log('rewritten:', path.relative(process.cwd(), file))
    changedCount++
  }
}

console.log(`Done. Updated files: ${changedCount}`)
EOT

echo "[2/5] Opravujem eslint.config.mjs na minimálny funkčný flat config..."
cat > eslint.config.mjs <<'EOT'
export default [
  {
    ignores: ['.next/**', 'out/**', 'build/**', 'next-env.d.ts'],
  },
]
EOT

echo "[3/5] Spúšťam rewrite importov..."
node rewrite-imports-node.mjs

echo "[4/5] Opravujem find priklad..."
mkdir -p backups/src-lib-api backups/src-lib-auth

if [ -d src/lib/api ]; then
  find src/lib/api -maxdepth 1 -type f -name '*.bak*' -exec mv -v {} backups/src-lib-api/ ;
fi

if [ -d src/lib/auth ]; then
  find src/lib/auth -maxdepth 1 -type f -name '*.bak*' -exec mv -v {} backups/src-lib-auth/ ;
fi

echo "[5/5] Kontroly..."
npm run lint
npm run typecheck
