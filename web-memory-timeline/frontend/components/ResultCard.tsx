import { buildTextFragment } from '../lib/highlight'

export default function ResultCard({ result }: { result: any }) {
  const frag = buildTextFragment(result.snippet || '')
  const href = `${result.url}${frag}`
  const sim = typeof result.similarity === 'number' ? (result.similarity * 100).toFixed(1) + '%' : ''

  return (
    <a href={href} target="_blank" rel="noreferrer" className="block border rounded p-3 hover:bg-gray-50">
      <div className="text-sm text-gray-500">{sim}</div>
      <div className="font-medium">{result.title || result.url}</div>
      <div className="text-sm text-gray-700 truncate">{result.snippet}</div>
    </a>
  )
}
