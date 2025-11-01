"use client"
import { useCallback } from 'react'

export default function SearchBar({ value, onChange, onSubmit }: { value: string; onChange: (v: string) => void; onSubmit: () => void }) {
  const onKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') onSubmit()
  }, [onSubmit])

  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        className="flex-1 border rounded px-3 py-2"
        placeholder="Search your web memory…"
      />
      <button onClick={onSubmit} className="px-3 py-2 rounded bg-black text-white">Search</button>
    </div>
  )
}
