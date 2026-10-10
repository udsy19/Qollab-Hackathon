#!/usr/bin/env node
// A closed pipe is not an error: `node scripts/x.mjs | head` must not report failure.
process.stdout.on('error', (e) => { if (e && e.code === 'EPIPE') process.exit(0) })
// Every hackathon project folder must be uploadable to Qollab as is and eligible to win. This
// checks the rules that can be checked from the files, so a project cannot drift out of them:
// Qollab's runtime rules (vault/Research/qollab-platform-and-submission.md) and the hackathon's
// (.claude/rules/hackathon-eligibility.md).
//
//   node scripts/gates/qollab-submission.mjs                 every project folder in the repo
//   node scripts/gates/qollab-submission.mjs <dir>...        these folders
//   node scripts/gates/qollab-submission.mjs --template      the project template (FILL: markers allowed)
//   node scripts/gates/qollab-submission.mjs --selftest      the template passes; each broken fixture fails
//
// A project folder is a top-level directory with `main.py` or `index.html` at its root: Qollab
// uploads the folder as the project, and only top-level entry files count.
// Exit: 0 every project passes · 1 a rule failed · 2 refused (bad argument, missing dir) ·
// 77 skip (no project folders yet — never a pass).
//
// CEILING — what this cannot see, so a pass does not claim it: whether the project RUNS on
// Qollab (Pyodide) or on IonQ's simulator; a backend.run inside a loop (only call sites are
// counted); data-file paths built at runtime; whether the demo video is public; the page's
// accessibility. Those are proven by a real run on Qollab and by looking.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..')
const TEMPLATE = path.join(ROOT, 'templates/qollab-project')
const NOT_PROJECTS = new Set(['vault', 'scripts', 'evidence', 'templates', 'node_modules'])
const DROPPED = new Set(['.git', '__MACOSX', '.DS_Store'])   // Qollab drops these on upload
const ATTRIBUTION = 'This effort is supported by Qollab & IonQ'
const MAX_FILES = 100, MAX_FILE_BYTES = 2 * 1024 * 1024, MAX_README = 65000

function listFiles(dir, rel = '') {
  const out = []
  for (const e of fs.readdirSync(path.join(dir, rel), { withFileTypes: true })) {
    if (DROPPED.has(e.name)) continue
    const r = rel ? `${rel}/${e.name}` : e.name
    if (e.isDirectory()) out.push(...listFiles(dir, r))
    else out.push(r)
  }
  return out
}

// Prose lines that are not markdown structure. Two in a row = a hard-wrapped paragraph, which
// Qollab (marked, breaks: true) renders as ragged short lines.
const STRUCTURE = /^\s*([#>|!*+-]|\d+[.)]\s|```|<|\[[^\]]*\]:)/
function hardWrapped(md) {
  let fence = false, prev = false
  for (const [i, line] of md.split('\n').entries()) {
    if (/^\s*```/.test(line)) { fence = !fence; prev = false; continue }
    const prose = !fence && line.trim() !== '' && !STRUCTURE.test(line)
    if (prose && prev) return i + 1
    prev = prose
  }
  return 0
}

const REQ_LINE = /^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?\s*((==|>=|<=|~=|!=|<|>)\s*[A-Za-z0-9.*+!-]+(\s*,\s*(==|>=|<=|~=|!=|<|>)\s*[A-Za-z0-9.*+!-]+)*)?$/
const SECRET = /(IONQ_API_KEY|IONQ_API_TOKEN|QISKIT_IONQ_API_TOKEN)\s*[=:]\s*['"][^'"]+['"]|\bsk-[A-Za-z0-9_-]{20,}|IonQProvider\(\s*(token\s*=\s*)?['"]/
const OWN_REMOTE = /IonQProvider\(|\.get_backend\(|QiskitRuntimeService\(/
const OWN_LOCAL = /\b(AerSimulator|BasicSimulator|StatevectorSampler|LocalSimulator)\(/

function check(dir, { allowFill = false } = {}) {
  const fails = []
  const fail = (m) => fails.push(m)
  const has = (f) => fs.existsSync(path.join(dir, f))
  const read = (f) => fs.readFileSync(path.join(dir, f), 'utf8')

  const py = has('main.py'), js = has('index.html') && has('main.js')
  if (!py && !js) fail('no entry point at the folder root: main.py, or index.html + main.js (files in subfolders do not count)')
  if (has('index.html') && !has('main.js')) fail('index.html without main.js: Qollab needs both for a JS project')

  if (!has('LICENSE')) fail('no LICENSE file (the hackathon requires MIT)')
  else if (!/MIT License/.test(read('LICENSE'))) fail('LICENSE is not the MIT License')

  if (!has('README.md')) fail('no README.md (it becomes the Qollab project page)')
  else {
    const md = read('README.md')
    if (md.length > MAX_README) fail(`README.md is ${md.length} chars; Qollab refuses more than ${MAX_README}`)
    if (!md.includes(ATTRIBUTION)) fail(`README.md lacks the required attribution, verbatim: "${ATTRIBUTION}"`)
    if (!/^#+\s.*how to run/im.test(md)) fail('README.md has no "How to run" section')
    if (!/^#+\s.*(prior work|built during)/im.test(md)) fail('README.md has no prior-work disclosure section ("Built during the hackathon / prior work")')
    if (!/^#+\s.*what'?s new/im.test(md)) fail('README.md has no "What\'s new here" section naming the novelty category')
    const w = hardWrapped(md)
    if (w) fail(`README.md line ${w} continues a hard-wrapped paragraph; Qollab renders each newline as a break — one paragraph per line`)
    if (!allowFill) {
      if (/FILL:/.test(md)) fail('README.md still has FILL: placeholders')
      if (!/https:\/\/(www\.)?(youtu\.be|youtube\.com)\//.test(md)) fail('README.md has no YouTube demo video link (the only host the page can embed)')
    }
  }

  if (!has('requirements.txt')) fail('no requirements.txt (pin the Qiskit range the project was tested on)')
  else for (const [i, raw] of read('requirements.txt').split('\n').entries()) {
    const line = raw.replace(/#.*/, '').trim()
    if (line && !REQ_LINE.test(line)) fail(`requirements.txt line ${i + 1} "${line}": Qollab accepts only name or name<op>version (no pip options, markers or URLs)`)
  }

  const files = listFiles(dir)
  if (files.length > MAX_FILES) fail(`${files.length} files; Qollab allows ${MAX_FILES} per project`)
  for (const f of files) {
    if (/(^|\/)(\.venv|venv|node_modules)\//.test(f)) { fail(`${f.split('/')[0]}/… is inside the project folder; it would be uploaded`); break }
  }
  let runs = 0
  for (const f of files) {
    const size = fs.statSync(path.join(dir, f)).size
    if (size > MAX_FILE_BYTES) fail(`${f} is ${(size / 1048576).toFixed(1)} MB; Qollab allows 2 MB per file`)
    if (/(^|\/)(\.venv|venv|node_modules)\//.test(f)) continue
    if (!/\.(py|js|mjs|html|txt|md|json|cfg|toml|ya?ml|env)$/.test(f) && !f.startsWith('.env')) continue
    const src = fs.readFileSync(path.join(dir, f), 'utf8')
    if (SECRET.test(src)) fail(`${f}: looks like an API key or token; published Qollab code must hold none`)
    if (!/\.(py|js|mjs)$/.test(f)) continue
    const lines = src.split('\n')
    lines.forEach((l, i) => {
      if (/^\s*#|^\s*\/\//.test(l)) return
      if (OWN_REMOTE.test(l)) fail(`${f}:${i + 1}: builds its own remote backend; use the pre-created \`backend\` Qollab supplies`)
      if (OWN_LOCAL.test(l)) {
        const guard = lines.slice(Math.max(0, i - 4), i).some((p) => /except\s+NameError/.test(p))
        if (!guard) fail(`${f}:${i + 1}: builds its own simulator outside an \`except NameError\` fallback; on Qollab that ignores the Select QPU choice`)
      }
      runs += (l.match(/\bbackend\.run\(/g) || []).length
    })
  }
  if (runs > 1) fail(`${runs} backend.run( call sites; IonQ backends accept one job per run — batch every circuit into one call`)

  if (py) {
    const src = read('main.py')
    const defs = src.match(/^\s*def main\s*\(.*$/gm) || []
    for (const d of defs) {
      if (/^\s/.test(d)) { fail('main.py: `def main(` must start at column 0 or Qollab never calls it'); continue }
      if (!/\)\s*(->\s*[^:]+)?:\s*(#.*)?$/.test(d)) { fail('main.py: the `def main(...)` signature must be on ONE line or Qollab silently never calls it'); continue }
      const params = d.replace(/^def main\s*\(/, '').replace(/\)\s*(->\s*[^:]+)?:\s*(#.*)?$/, '').trim()
      if (params) for (const p of params.split(',')) {
        if (!/^\s*[A-Za-z_]\w*\s*:\s*(int|float|str|bool)\s*(=\s*.+)?$/.test(p)) fail(`main.py: main() parameter "${p.trim()}" must be annotated int, float, str or bool`)
      }
    }
    if (defs.length && /^(?!\s*def\b).*\bmain\s*\(\s*\)/m.test(src.replace(/^\s*#.*$/gm, ''))) fail('main.py calls main() itself; Qollab already calls it — a second call is a second IonQ job')
  }
  return fails
}

function projectDirs() {
  return fs.readdirSync(ROOT, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !NOT_PROJECTS.has(e.name))
    .map((e) => path.join(ROOT, e.name))
    .filter((d) => fs.existsSync(path.join(d, 'main.py')) || fs.existsSync(path.join(d, 'index.html')))
}

function report(dirs, opts) {
  let failed = 0
  for (const d of dirs) {
    const fails = check(d, opts)
    const name = path.relative(ROOT, d) || d
    if (fails.length) { failed++; console.log(`  FAIL ${name}`); for (const f of fails) console.log(`         ${f}`) }
    else console.log(`  ok   ${name}`)
  }
  return failed
}

function edit(d, f, fn) { const p = path.join(d, f); fs.writeFileSync(p, fn(fs.readFileSync(p, 'utf8'))) }

function selftest() {
  let bad = 0
  const expect = (label, cond) => { console.log(`  ${cond ? 'ok  ' : 'FAIL'} ${label}`); if (!cond) bad++ }
  expect('template passes (FILL: allowed)', check(TEMPLATE, { allowFill: true }).length === 0)
  expect('template fails as a submission (FILL: left, no video)', check(TEMPLATE).some((f) => /FILL:/.test(f)))
  const cases = [
    ['no LICENSE', (d) => fs.rmSync(path.join(d, 'LICENSE')), /LICENSE/],
    ['no attribution', (d) => edit(d, 'README.md', (s) => s.replace(ATTRIBUTION, '')), /attribution/],
    ['hard-wrapped README', (d) => edit(d, 'README.md', (s) => s.replace('## What it shows\n\n', '## What it shows\n\nfirst half of a paragraph\nsecond half\n\n')), /hard-wrapped/],
    ['two-line main signature', (d) => edit(d, 'main.py', (s) => s.replace('def main(shots: int = 1024):', 'def main(\n    shots: int = 1024):')), /ONE line/],
    ['unannotated main parameter', (d) => edit(d, 'main.py', (s) => s.replace('shots: int = 1024', 'shots=1024')), /annotated/],
    ['second backend.run', (d) => edit(d, 'main.py', (s) => s + '\n    backend.run(circuit)\n'), /one job per run/],
    ['hardcoded IonQ key', (d) => edit(d, 'main.py', (s) => s + '\nIONQ_API_KEY = "abc123"\n'), /API key/],
    ['own IonQ backend', (d) => edit(d, 'main.py', (s) => s + '\nprovider = IonQProvider()\n'), /remote backend/],
    ['unguarded local simulator', (d) => edit(d, 'main.py', (s) => s + '\nsim = AerSimulator()\n'), /except NameError/],
    ['main() self-call', (d) => edit(d, 'main.py', (s) => s + '\nmain()\n'), /calls main\(\) itself/],
    ['pip option in requirements', (d) => edit(d, 'requirements.txt', (s) => s + '--extra-index-url https://x\n'), /requirements/],
    ['.venv inside the project', (d) => { fs.mkdirSync(path.join(d, '.venv/lib'), { recursive: true }); fs.writeFileSync(path.join(d, '.venv/lib/x.py'), '') }, /\.venv/],
    ['no entry point', (d) => fs.rmSync(path.join(d, 'main.py')), /entry point/],
  ]
  for (const [label, breakIt, want] of cases) {
    const d = fs.mkdtempSync(path.join(os.tmpdir(), 'qollab-selftest-'))
    fs.cpSync(TEMPLATE, d, { recursive: true })
    breakIt(d)
    const fails = check(d, { allowFill: true })
    expect(`${label} → caught`, fails.some((f) => want.test(f)))
    fs.rmSync(d, { recursive: true, force: true })
  }
  console.log(bad ? `QOLLAB-SUBMISSION SELFTEST FAIL (${bad})` : 'QOLLAB-SUBMISSION SELFTEST PASS')
  return bad ? 1 : 0
}

const argv = process.argv.slice(2)
if (argv[0] === '--selftest') process.exit(selftest())
if (argv[0] === '--template') {
  const n = report([TEMPLATE], { allowFill: true })
  console.log(n ? 'QOLLAB-SUBMISSION FAIL (template)' : 'QOLLAB-SUBMISSION PASS (template)')
  process.exit(n ? 1 : 0)
}
for (const a of argv) if (a.startsWith('-')) { console.log(`qollab-submission: unrecognised argument '${a}' — accepts: [dir...] --template --selftest`); process.exit(2) }
const dirs = argv.length ? argv.map((a) => path.resolve(a)) : projectDirs()
for (const d of dirs) if (!fs.existsSync(d)) { console.log(`QOLLAB-SUBMISSION REFUSED: no such folder ${d}`); process.exit(2) }
if (!dirs.length) { console.log('QOLLAB-SUBMISSION SKIP — no project folders yet (a top-level dir with main.py or index.html)'); process.exit(77) }
const n = report(dirs, {})
console.log(n ? `QOLLAB-SUBMISSION FAIL — ${n} of ${dirs.length} project(s)` : `QOLLAB-SUBMISSION PASS — ${dirs.length} project(s)`)
process.exit(n ? 1 : 0)
