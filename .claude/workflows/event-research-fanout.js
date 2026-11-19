export const meta = {
  name: 'event-research-fanout',
  description: '/event-deep-research Steps 2 + 2.5: four research specialists in parallel, then the synthesizer',
  whenToUse: 'Only from /event-deep-research after Alex approves the triage plan (Step 1.5) and Step 1.7 has run. Read-only: no Notion, HubSpot or spine writes.',
  phases: [
    { title: 'Research', detail: 'company, person, topic and signal specialists in parallel; one deeper retry for a thin return' },
    { title: 'Synthesize', detail: 'event-research-synthesizer builds the Scan head and the Evidence Set' },
  ],
}

// Why a workflow: the fan-out was four Agent calls the parent assembled by hand each run.
// Here the dispatch shape is fixed in code, every specialist return is schema-checked, and the Evidence Ledger is
// rendered by code in the one bullet form Step 4.2's parser expects (the 2026-09-27 run where every specialist
// emitted tables and the graph write found 0 admissible rows can't recur). The parent still owns the run
// (invariant 6): it launches this after the triage gate and gets back only the synthesizer's two blocks plus the
// rendered specialist returns. Every agent here is read-only; nothing in this script writes anywhere.
//
// args (built by the parent at Step 2; see the command):
// {
//   event: { name, date },                       // date YYYY-MM-DD
//   verbatim_source: "<the VERBATIM SOURCE block, unedited>",
//   focus: "<Alex's stated focus or ''>",
//   triage_plan: "<the approved triage plan, as text>",
//   prior_pack: "<Step 1.7 Prior-Context Pack, or '' for a first-touch event>",
//   specialists: {
//     company: { entities: "<entity list + triage path per entity, or ''>", prior: "<Companies cards or ''>" },
//     person:  { entities: "...", prior: "<People cards>" },
//     topic:   { entities: "...", prior: "<Topic cards>" },
//     signal:  { entities: "<ALL companies, SKIP included>", prior: "<Graph Signals + Continuity Ledger>" }
//   }
// }

const A = args || {}
if (!A.event || !A.event.name || !A.verbatim_source || !A.specialists) {
  throw new Error('event-research-fanout: args need event.name, verbatim_source and specialists (see the header)')
}

const SPECIALISTS = [
  { key: 'company', agentType: 'company-researcher', label: 'company-researcher',
    scope: 'Every Company entity below that needs research (NEW, REFRESH, or FRAME-ONLY).' },
  { key: 'person', agentType: 'person-researcher', label: 'person-researcher',
    scope: 'Every Person entity below that needs research (NEW or REFRESH).' },
  { key: 'topic', agentType: 'topic-landscape-analyst', label: 'topic-landscape-analyst',
    scope: 'Every Topic entity below (NEW, REFRESH, or APPEND-CURRENT-EVENTS-ONLY). Topics never get a full SKIP.' },
  { key: 'signal', agentType: 'competitive-signal-scanner', label: 'competitive-signal-scanner',
    scope: 'ALL companies below, including SKIP ones: market signals from the last 60 days.' },
]

const TIERS = ['web-verified', 'email-signal', 'notion-prior', 'inference']

const SPECIALIST_SCHEMA = {
  type: 'object',
  properties: {
    report: { type: 'string', description: 'Your full prose return per your agent contract: findings per entity, the historical spine (lineage / founding-funding-evolution arc / career arc, with dates), and the mechanism + jargon material for the novice on-ramp. Do NOT put the Evidence Ledger here.' },
    ledger: {
      type: 'array',
      description: 'The Evidence Ledger: one row per specific, recent or contestable claim, for every entity you researched.',
      items: {
        type: 'object',
        properties: {
          entity: { type: 'string', description: 'Exact entity name as given in your entity list' },
          claim: { type: 'string', description: 'The claim in 15 words or fewer' },
          tier: { type: 'string', enum: TIERS },
          source: { type: 'string', description: 'Site or source name' },
          url: { type: 'string', description: 'Full URL. Mandatory for web-verified; empty string only for email-signal without a public URL, notion-prior or inference.' },
          date: { type: 'string', description: 'YYYY-MM-DD of the source' },
        },
        required: ['entity', 'claim', 'tier', 'source', 'url', 'date'],
      },
    },
    thin: { type: 'boolean', description: 'true if you could not find enough to cover your entities properly' },
  },
  required: ['report', 'ledger', 'thin'],
}

const SYNTH_SCHEMA = {
  type: 'object',
  properties: {
    scan_head: { type: 'string', description: 'The Scan head, exactly as your contract defines it: Quick Take, People at-a-glance, Questions to ask, Success Signals, Verification Flags.' },
    evidence_set: { type: 'string', description: 'The ## Evidence Set block: URL-carrying, organised by Deep-Read render section, keeping every ##### Evidence Ledger — <Entity Name> heading and bullet verbatim.' },
  },
  required: ['scan_head', 'evidence_set'],
}

function block(title, body) { return body && String(body).trim() ? `### ${title}\n${String(body).trim()}\n` : '' }

function specialistPrompt(s, slice, deeper) {
  return [
    `Event: ${A.event.name} (${A.event.date || 'date unknown'}). You are the ${s.label} in the /event-deep-research Step 2 fan-out.`,
    '',
    '### (1) VERBATIM SOURCE: the source of truth',
    'Read every line. Derive findings from THIS text; the framing below is supplementary, not a replacement.',
    '"""',
    A.verbatim_source,
    '"""',
    '',
    block(`(2–3) Your entities and their triage paths. ${s.scope}`, slice.entities),
    block("(5) Alex's stated focus", A.focus),
    block('(6) Your slice of the Prior-Context Pack', slice.prior
      ? `${slice.prior}\n\nTreat KNOWN as starting context and STALE / UNVERIFIED as leads to refresh or verify with web search. Never restate UNVERIFIED as fact.`
      : ''),
    'Return per your agent contract, through the StructuredOutput tool: the prose return in `report`, and the Evidence Ledger as structured rows in `ledger` (the parent renders them; do not also write a ledger table or bullets in `report`). Every web-verified row carries its full URL.',
    deeper ? `\nThis is a DEEPER second pass: your first return was thin (${deeper}). Go broader on sources (company blog, filings, press, podcasts, GitHub, conference talks) and cover every entity in your list.` : '',
  ].filter(Boolean).join('\n')
}

// Deterministic checks, in code: what counts as thin, and which ledger rows are admissible.
function audit(slice, r) {
  if (!r) return { thin: 'no return', admissible: [], dropped: [] }
  const admissible = [], dropped = []
  for (const row of r.ledger || []) {
    const words = String(row.claim || '').trim().split(/\s+/).filter(Boolean).length
    if (row.tier === 'web-verified' && !/^https?:\/\//.test(row.url || '')) dropped.push({ row, why: 'web-verified without a URL' })
    else if (!/^\d{4}-\d{2}-\d{2}$/.test(row.date || '')) dropped.push({ row, why: 'date not YYYY-MM-DD' })
    else if (words === 0 || words > 15) dropped.push({ row, why: `claim is ${words} words` })
    else admissible.push(row)
  }
  let thin = ''
  if (r.thin) thin = 'specialist flagged its own return as thin'
  else if (String(r.report || '').length < 1500) thin = `report is ${String(r.report || '').length} chars`
  else if (admissible.length === 0) thin = 'no admissible ledger rows'
  return { thin, admissible, dropped }
}

// Step 4.2's contract: `##### Evidence Ledger — <Entity Name>` then one bullet per row, exactly this shape.
function renderLedger(rows) {
  const byEntity = new Map()
  for (const row of rows) {
    if (!byEntity.has(row.entity)) byEntity.set(row.entity, [])
    byEntity.get(row.entity).push(row)
  }
  // One line per row: a newline inside a field would split the row and the parser would drop it.
  const one = v => String(v || '').replace(/\s+/g, ' ').trim()
  return [...byEntity.entries()].map(([entity, rs]) =>
    `##### Evidence Ledger — ${one(entity)}\n` +
    rs.map(r => `- claim: ${one(r.claim)} | tier: ${r.tier} | source: ${one(r.source)} | url: ${one(r.url)} | date: ${r.date}`).join('\n')
  ).join('\n\n')
}

phase('Research')
const active = SPECIALISTS.filter(s => {
  const slice = A.specialists[s.key]
  return slice && String(slice.entities || '').trim()
})
const skipped = SPECIALISTS.filter(s => !active.includes(s)).map(s => s.label)
if (skipped.length) log(`No entities for: ${skipped.join(', ')}; not dispatched.`)

// Barrier on purpose: the synthesizer needs all four returns together.
const results = await parallel(active.map(s => async () => {
  const slice = A.specialists[s.key]
  let r = await agent(specialistPrompt(s, slice), { label: s.label, phase: 'Research', agentType: s.agentType, schema: SPECIALIST_SCHEMA })
  let a = audit(slice, r)
  let retried = false
  if (a.thin) {
    log(`${s.label}: thin (${a.thin}); one deeper pass`)
    retried = true
    const r2 = await agent(specialistPrompt(s, slice, a.thin), { label: `${s.label} (deeper)`, phase: 'Research', agentType: s.agentType, schema: SPECIALIST_SCHEMA })
    const a2 = audit(slice, r2)
    if (r2 && (!r || a2.admissible.length >= a.admissible.length)) { r = r2; a = a2 }
  }
  if (!r) return { s, failed: true, retried }
  return { s, retried, thin: a.thin, report: r.report, admissible: a.admissible, dropped: a.dropped }
}))

const done = results.filter(Boolean).filter(x => !x.failed)
const failed = results.filter(Boolean).filter(x => x.failed).map(x => x.s.label)
  .concat(results.map((x, i) => x ? null : active[i].label).filter(Boolean))
if (!done.length) throw new Error(`event-research-fanout: every specialist failed (${failed.join(', ')})`)

const specialistText = done.map(x =>
  `## ${x.s.label} return\n\n${x.report.trim()}\n\n${renderLedger(x.admissible)}`
).join('\n\n---\n\n')

phase('Synthesize')
const synth = await agent([
  `Event: ${A.event.name} (${A.event.date || 'date unknown'}). You are the event-research-synthesizer at /event-deep-research Step 2.5.`,
  '', '### Raw invite (VERBATIM SOURCE)', '"""', A.verbatim_source, '"""', '',
  block('Approved triage plan', A.triage_plan),
  block("Alex's stated focus", A.focus),
  block('Step 1.7 Prior-Context Pack (Continuity Ledger and Graph Signals especially)', A.prior_pack),
  failed.length ? `### Missing specialists\n${failed.join(', ')} failed and returned nothing. Say so in Verification Flags.\n` : '',
  '### Specialist returns (each ends with its Evidence Ledger in the canonical bullet form)',
  specialistText,
  '',
  'Return the two blocks per your contract through the StructuredOutput tool: `scan_head` and `evidence_set`. In the Evidence Set keep every `##### Evidence Ledger — <Entity Name>` heading and bullet exactly as given; Step 4.2 parses them.',
].filter(Boolean).join('\n'), { label: 'event-research-synthesizer', phase: 'Synthesize', agentType: 'event-research-synthesizer', schema: SYNTH_SCHEMA })

if (!synth) throw new Error('event-research-fanout: the synthesizer returned nothing; specialist returns are in the journal')

const dropped = done.flatMap(x => x.dropped.map(d => `${x.s.label} · ${d.row.entity} · ${d.why}: ${d.row.claim}`))
if (dropped.length) log(`${dropped.length} ledger rows dropped as inadmissible (listed in audit.dropped)`)

return {
  scan_head: synth.scan_head,
  evidence_set: synth.evidence_set,
  // Step 4.2a fallback when the Evidence Set lost its ledger headings: write this instead.
  specialist_returns: specialistText,
  audit: {
    dispatched: active.map(s => s.label),
    not_dispatched: skipped,
    failed,
    retried: done.filter(x => x.retried).map(x => x.s.label),
    still_thin: done.filter(x => x.thin).map(x => `${x.s.label}: ${x.thin}`),
    ledger_rows: Object.fromEntries(done.map(x => [x.s.label, x.admissible.length])),
    dropped,
  },
}
