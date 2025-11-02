#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'

const out = process.argv[2] || 'visits_large.json'

const topics = [
  {
    title: 'Vector Search & Databases',
    pages: [
      ['https://pgvector.dev', 'pgvector', 'Open-source vector similarity search for Postgres.'],
      ['https://faiss.ai', 'FAISS', 'Facebook AI Similarity Search for vector databases.'],
      ['https://supabase.com/docs', 'Supabase Docs', 'Postgres, auth, storage, edge functions.'],
      ['https://www.postgresql.org/docs/', 'PostgreSQL Docs', 'SQL, indexes, extensions, performance.']
    ]
  },
  {
    title: 'Embeddings & LLM Infra',
    pages: [
      ['https://ollama.com', 'Ollama', 'Run open-source models locally.'],
      ['https://huggingface.co/docs', 'Hugging Face Docs', 'Models, datasets, inference.'],
      ['https://python.langchain.com/docs/', 'LangChain Docs', 'Build LLM apps with tools and memory.'],
      ['https://platform.openai.com/docs/overview', 'OpenAI Platform', 'API, models, embeddings.']
    ]
  },
  {
    title: 'Web Dev & Frameworks',
    pages: [
      ['https://nextjs.org/docs', 'Next.js Docs', 'React framework, App Router, data fetching.'],
      ['https://developer.mozilla.org/', 'MDN Web Docs', 'HTML, CSS, JS reference.'],
      ['https://tailwindcss.com/docs', 'Tailwind Docs', 'Utility-first CSS framework.'],
      ['https://react.dev/learn', 'React Docs', 'Modern React patterns, hooks.']
    ]
  },
  {
    title: 'Cloud & Data',
    pages: [
      ['https://cloud.google.com/docs', 'Google Cloud Docs', 'Cloud products, APIs, services.'],
      ['https://docs.aws.amazon.com/', 'AWS Docs', 'Services, SDKs, guides.'],
      ['https://learn.microsoft.com/azure/', 'Azure Docs', 'Azure services and reference.'],
      ['https://kubernetes.io/docs/', 'Kubernetes Docs', 'Containers, orchestration, workloads.']
    ]
  },
  {
    title: 'Programming Languages',
    pages: [
      ['https://docs.python.org/3/', 'Python Docs', 'Standard library, language reference.'],
      ['https://go.dev/doc/', 'Go Docs', 'Tour, packages, tooling.'],
      ['https://docs.rs/', 'Rust Docs', 'Crates and Rust documentation.'],
      ['https://nodejs.org/en/docs', 'Node.js Docs', 'API reference and guides.']
    ]
  }
]

// Produce ~30 sessions by repeating topics with slight variations
const sessions = []
let baseTs = Date.now() - 1000 * 60 * 60 * 24 * 30 // last 30 days
let sid = 0
for (let i = 0; i < 30; i++) {
  const t = topics[i % topics.length]
  const start = baseTs + i * (15 * 60 * 1000)
  const pages = t.pages.map((p, idx) => ({
    url: p[0],
    title: p[1],
    snippet: p[2],
    ts: start + idx * (2 * 60 * 1000)
  }))
  const end = pages[pages.length - 1].ts
  sessions.push({ id: `sess_${++sid}`, start, end, sessionTitle: t.title, pages })
}

const outPath = path.resolve(process.cwd(), out)
fs.writeFileSync(outPath, JSON.stringify(sessions, null, 2))
console.log(`Wrote ${outPath} with ${sessions.length} sessions`)
