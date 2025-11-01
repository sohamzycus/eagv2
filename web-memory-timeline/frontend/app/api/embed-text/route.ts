import { NextRequest } from 'next/server'

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
const OLLAMA_EMBED_MODEL = process.env.OLLAMA_EMBED_MODEL || 'nomic-embed-text'

export async function POST(req: NextRequest) {
  try {
    const { text } = await req.json()
    if (!text || typeof text !== 'string') {
      return new Response(JSON.stringify({ error: 'missing text' }), { status: 400 })
    }
    const body = JSON.stringify({ model: OLLAMA_EMBED_MODEL, prompt: String(text).slice(0, 4000) })
    const r = await fetch(`${OLLAMA_BASE_URL}/api/embeddings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body
    })
    if (!r.ok) {
      const t = await r.text()
      return new Response(JSON.stringify({ error: 'ollama failed', details: t }), { status: 500 })
    }
    const data = await r.json()
    return new Response(JSON.stringify({ embedding: data.embedding }), { headers: { 'Content-Type': 'application/json' } })
  } catch (e: any) {
    return new Response(JSON.stringify({ error: String(e) }), { status: 500 })
  }
}
