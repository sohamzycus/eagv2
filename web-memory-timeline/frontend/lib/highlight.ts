function encodeFragment(text: string) {
  return encodeURIComponent(text.replace(/\s+/g, ' ').trim())
}

export function buildTextFragment(snippet: string) {
  if (!snippet) return ''
  const s = snippet.trim()
  if (!s) return ''
  const windowSize = 80
  const sub = s.slice(0, windowSize)
  return `#:~:text=${encodeFragment(sub)}`
}
