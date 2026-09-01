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

function walk(dir, out) {
  if (!out) out = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.next') continue
      walk(full, out)
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      out.push(full)
    }
  }
  return out
}

function rewriteSpecifier(spec) {
  const m = spec.match(/^@\/features\/([^/]+)\/.+$/)
  if (!m) return spec
  const feature = m[1]
  if (!featureNames.has(feature)) return spec
  return '@/features/' + feature
}

function rewriteContent(content) {
  let changed = false

  content = content.replace(
    /\b(from\s+['"])([^'"]+)(['"])/g,
    function (all, a, spec, c) {
      const next = rewriteSpecifier(spec)
      if (next !== spec) changed = true
      return a + next + c
    }
  )

  content = content.replace(
    /\b(import\s*\(\s*['"])([^'"]+)(['"]\s*\))/g,
    function (all, a, spec, c) {
      const next = rewriteSpecifier(spec)
      if (next !== spec) changed = true
      return a + next + c
    }
  )

  return { content: content, changed: changed }
}

const files = walk(root)
let changedCount = 0

for (const file of files) {
  const original = fs.readFileSync(file, 'utf8')
  const result = rewriteContent(original)
  if (result.changed) {
    fs.writeFileSync(file, result.content, 'utf8')
    console.log('rewritten: ' + path.relative(process.cwd(), file))
    changedCount++
  }
}

console.log('Done. Updated files: ' + changedCount)
