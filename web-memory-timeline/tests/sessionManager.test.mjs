import assert from 'node:assert'
import { findOrCreateSession } from '../extension/sessionManager.js'

const t0 = 1730448000000
let sessions = []

let r = findOrCreateSession(sessions, { url: 'https://a.com', title: 'A', snippet: 'a', ts: t0 })
sessions = r.sessions
assert.equal(sessions.length, 1)

r = findOrCreateSession(sessions, { url: 'https://b.com', title: 'B', snippet: 'b', ts: t0 + 5 * 60 * 1000 })
sessions = r.sessions
assert.equal(sessions.length, 1)
assert.equal(sessions[0].pages.length, 2)

r = findOrCreateSession(sessions, { url: 'https://c.com', title: 'C', snippet: 'c', ts: t0 + 21 * 60 * 1000 })
sessions = r.sessions
assert.equal(sessions.length, 2)

console.log('sessionManager tests passed')
