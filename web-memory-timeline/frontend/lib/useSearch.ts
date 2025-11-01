"use client"
import { useState } from 'react'
import { supabase } from './supabaseClient'

export function useSearch() {
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  async function embedQuery(query: string): Promise<number[]> {
    const res = await fetch('/api/embed-text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: query }) })
    if (!res.ok) throw new Error('embed failed')
    const data = await res.json()
    return data.embedding as number[]
  }

  async function search(q: string) {
    try {
      setLoading(true)
      setError(null)
      setResults([])
      const embedding = await embedQuery(q)
      const { data, error } = await supabase.rpc('match_pages', {
        query_embedding: embedding,
        match_threshold: 0,
        match_count: 20
      })
      if (error) throw error
      setResults(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  return { results, loading, error, search }
}
