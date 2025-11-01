#!/usr/bin/env node
/**
 * Ingests visits.json into Supabase (sessions + pages with embeddings).
 *
 * Usage:
 *   export SUPABASE_URL="https://<project>.supabase.co"
 *   export SUPABASE_SERVICE_ROLE_KEY="<service_role_key>"
 *   export OLLAMA_BASE_URL="http://localhost:11434"   # optional
 *   export OLLAMA_EMBED_MODEL="nomic-embed-text"       # optional
 *   node tools/ingest_visits_to_supabase.mjs visits.json
 */
import fs from 'node:fs'
import path from 'node:path'
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.SUPABASE_URL
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY
if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env')
  process.exit(1)
}

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
const OLLAMA_EMBED_MODEL = process.env.OLLAMA_EMBED_MODEL || 'nomic-embed-text'

const input = process.argv[2] || 'visits.json'
const inputPath = path.resolve(process.cwd(), input)
if (!fs.existsSync(inputPath)) {
  console.error('Input visits.json not found at', inputPath)
  process.exit(1)
}

const visits = JSON.parse(fs.readFileSync(inputPath, 'utf-8'))
console.log(`Loaded ${visits.length} sessions from ${input}`)

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  global: { headers: { 'X-Client-Info': 'web-memory-ingest' } }
})

async function embed(text) {
  const body = JSON.stringify({ model: OLLAMA_EMBED_MODEL, prompt: String(text).slice(0, 4000) })
  const r = await fetch(`${OLLAMA_BASE_URL}/api/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body
  })
  if (!r.ok) throw new Error(`Ollama error ${r.status}`)
  const data = await r.json()
  return data.embedding
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

for (const s of visits) {
  const { data: sessionRow, error: sessionErr } = await supabase
    .from('sessions')
    .insert({ start_ts: s.start, end_ts: s.end, title: s.sessionTitle || null })
    .select('id')
    .single()
  if (sessionErr) {
    console.error('Insert session failed:', sessionErr)
    process.exit(1)
  }
  const sessionId = sessionRow.id
  console.log('Inserted session', sessionId)

  const pages = Array.isArray(s.pages) ? s.pages : []
  for (const p of pages) {
    const text = `${p.title || p.url}\n${p.snippet || ''}\n${p.url}`
    let vector
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        vector = await embed(text)
        break
      } catch (e) {
        console.warn(`Embed retry ${attempt} for ${p.url}:`, e.message)
        await sleep(500 * attempt)
      }
    }
    if (!vector) {
      console.error('Failed to embed after retries, skipping', p.url)
      continue
    }

    const { error: pageErr } = await supabase
      .from('pages')
      .insert({
        session_id: sessionId,
        url: p.url,
        title: p.title || null,
        snippet: p.snippet || null,
        ts: p.ts || Date.now(),
        embedding: vector
      })
    if (pageErr) {
      console.error('Insert page failed:', pageErr)
      process.exit(1)
    }
    console.log('  + page', p.url)
  }
}

console.log('Ingest complete')
