#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

echo "[1/4] Prepisujem rewrite-imports-node.mjs..."
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

echo "[2/4] Inštalujem @eslint/eslintrc..."
npm install -D @eslint/eslintrc

echo "[3/4] Prepisujem eslint.config.mjs cez FlatCompat..."
cat > eslint.config.mjs <<'EOT'
import { FlatCompat } from '@eslint/eslintrc'

const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
})

const eslintConfig = [
  ...compat.extends('next/core-web-vitals'),
  {
    ignores: [
      '.next/**',
      'out/**',
      'build/**',
      'next-env.d.ts',
    ],
  },
]

export default eslintConfig
EOT

echo "[4/4] Spúšťam rewrite + lint + typecheck..."
node rewrite-imports-node.mjs
npm run lint
npm run typecheck
