"use client"
import { useState } from 'react'
import { useSearch } from '../lib/useSearch'
import SearchBar from '../components/SearchBar'
import ResultCard from '../components/ResultCard'

export default function Page() {
  const [query, setQuery] = useState("")
  const { results, loading, error, search } = useSearch()

  return (
    <main>
      <div className="mb-4">
        <SearchBar value={query} onChange={setQuery} onSubmit={() => search(query)} />
      </div>
      {loading && <div className="text-sm text-gray-500">Searching…</div>}
      {error && <div className="text-sm text-red-600">{String(error)}</div>}
      <div className="space-y-3">
        {results.map((r) => (
          <ResultCard key={r.id} result={r} />
        ))}
      </div>
    </main>
  )
}
