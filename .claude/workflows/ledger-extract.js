export const meta = {
  name: 'ledger-extract',
  description: 'YED-495: re-derive Evidence Ledger quotes from page text that code fetched, one no-tools agent per batch',
  phases: [{ title: 'Extract' }],
}
// Input (args): the "workflow_args" key that `.claude/scripts/ledger_refetch.py prepare` writes:
//   { batches: [[{ url, fetched, text, claims: [{ rid, entity, claim }] }, ...], ...] }
// Output: { rows: [{ rid, claim, quote } | { rid, none: true }] } for `ledger_refetch.py swap`.
// The extractor has no tools: it can quote only from the text in its prompt, which is what makes the quote proof.
const A = args || {}
const ROWS = { type: 'object', properties: { rows: { type: 'array', items: { type: 'object', properties: {
  rid: { type: 'string' }, none: { type: 'boolean' }, claim: { type: 'string' }, quote: { type: 'string' } },
  required: ['rid'] } } }, required: ['rows'] }
phase('Extract')
const out = await parallel((A.batches || []).map((b, i) => () => agent([
  'Work only from the page text in this message. Do not use any tools.',
  'Each PAGE below is the text of a web page as code fetched it. Under it are CLAIMS a researcher made citing that page, each with an id.',
  'For EACH claim id, return one row:',
  '- quote: a span of 6 to 25 words copied EXACTLY from that page text, character for character, that states the claim\'s fact. Never fix typos, never join distant fragments, never quote a different page.',
  '- claim: at most 15 words, written FROM the quote: it may assert only what the quote says. Keep the researcher\'s fact and subject; if the quote supports only part of it, write only that part. Every figure and every name in your claim, other than the ledger entity named with the claim, must appear in the quote as written. No dates or publisher names in the claim.',
  '- If no span of the page states the claim\'s fact, return { rid, none: true }. Never write an absence claim, and never guess.',
  'Return every claim id exactly once.',
  '', ...b.flatMap(p => [`===== PAGE ${p.url}`, p.text, '', 'CLAIMS:', ...p.claims.map(c => `[${c.rid}] (${c.entity}) ${c.claim}`), '']),
].join('\n'), { label: `extract:${i + 1}`, phase: 'Extract', schema: ROWS, model: 'sonnet' }).then(r => (r ? r.rows : []))))
const rows = out.flat()
const want = (A.batches || []).flatMap(b => b.flatMap(p => p.claims.map(c => c.rid)))
const missing = want.filter(id => !rows.find(r => r.rid === id))
if (missing.length) log(`${missing.length} claim ids came back with no row; swap treats them as none`)
return { rows, missing }
