#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'

const args = process.argv.slice(2)
const out = args[0] || 'visits.json'

function now() { return Date.now() }

function makeSession(id, pages) {
  const start = pages[0]?.ts || now()
  const end = pages[pages.length - 1]?.ts || start
  return { id, start, end, sessionTitle: pages[0]?.title || id, pages }
}

function makePage(url, title, snippet, ts) {
  return { url, title, snippet, ts }
}

function fromSample() {
  const samplePath = path.resolve(path.join(process.cwd(), 'samples', 'visits.sample.json'))
  if (fs.existsSync(samplePath)) {
    return JSON.parse(fs.readFileSync(samplePath, 'utf-8'))
  }
  const t = now()
  return [
    makeSession('sess_local', [ makePage('https://example.com', 'Example', 'Example Domain', t) ])
  ]
}

const data = fromSample()
fs.writeFileSync(out, JSON.stringify(data, null, 2))
console.log(`Wrote ${out} (${data.length} sessions)`)
