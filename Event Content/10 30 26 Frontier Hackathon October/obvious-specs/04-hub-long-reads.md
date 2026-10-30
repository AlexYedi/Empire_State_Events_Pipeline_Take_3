# 04 · Hub Long Reads (empire-state-hub) · Tier 3, Track B feature

Written in Obvious's three phases. **Alex: edit the Product phase on the train. It's your lever.**

---

## Phase 1 · Product

**Problem.** Each event post on LinkedIn tops out at 3,000 characters and a 4:5 PDF. The Learn-More link in
the first comment has nowhere rich to land. Readers who want depth leave.

**Goal.** Every event gets a web-native long read on the Hub: the long form of its post, amended after the event,
and the destination of the Learn-More link.

**Users.** (1) LinkedIn readers clicking Learn More. (2) Hiring managers and peers judging the depth of Alex's
thinking. (3) Alex, who needs to publish one from a reviewed file in minutes.

**In scope (v1).**
- A long read is a committed, reviewed JSON file per room. It is never pulled live from Notion (Notion holds private context).
- A typed block model: heading, paragraph, pull-quote (with attribution), image (with alt and caption), callout,
  stat (value + label + source), and link list (sources).
- A page at `/rooms/<slug>/read`, plus a "Read the long read" link on the room page when one exists.
- One seed long read, published only from public text (a post already published on LinkedIn).

**Out of scope (v1).** Interactive charts, video, 3D, comments, authoring UI, Notion sync.

**Success.** The seed renders. Adding a second long read takes only a new JSON file. The public-safe check stays green.

**Hard constraints.** Public-safe by construction: no email or phone fields exist in the schema; no recorded
speech; quotes only where attributed. `scripts/verify-public-safe.mjs` already scans `src/data/**`, so put the files there.
Do **not** edit that script.

---

## Phase 2 · UX

- **Reading layout.** Single column, ~68ch measure, house display/body fonts, dark and light themes from the existing tokens.
- **Header.** Event name, date, venue (from the room), series pill, reading time, and a "Back to room" link.
- **Blocks.** Pull-quotes get the acid-green left rule. Stats render as a large mono number with the label and source beneath.
  Images are lazy-loaded with captions. Sources render as a numbered list at the end.
- **Room page.** A "Read the long read →" link under the room title, only when a long read exists.
- **Mobile.** No horizontal scroll at 375px, with a 16px side gutter.
- **Accessibility.** Semantic `article`/`h2`/`blockquote`/`figure`; every image needs alt text (the schema enforces it).

---

## Phase 3 · Technical

- **Data.** `src/data/long-reads/<slug>.json`, where `<slug>` must match an existing room slug.
- **Schema.** `src/lib/long-reads.ts`: a zod discriminated union on `type` for the blocks above; a top-level
  `{ slug, updated, readingMinutes?, blocks[] }`. Parse at import so a malformed file fails the build (same idiom as `src/lib/rooms.ts`).
- **Loader.** `getLongRead(slug)` and `hasLongRead(slug)`; `readingMinutes` is computed when omitted.
- **Route.** `src/app/(public)/rooms/[slug]/read/page.tsx` with `generateStaticParams` over the slugs that have a file,
  `dynamicParams = false`, and `generateMetadata` from the room.
- **Components.** `src/components/long-read/` with one component per block type.
- **Tests.** A `node --test` file next to the rooms test: a valid fixture parses; a missing alt, an unknown block type and a
  slug with no matching room each fail. Wire it into `pnpm check`.
- **Seed.** `src/data/long-reads/<seed-slug>.json`. **Alex supplies the slug and the published post text at plan approval.**
  Until then, use a clearly fake fixture under `scripts/fixtures/`, never under `src/data/`.

**Suggested executables.** (1) Schema + loader + tests. (2) Block components. (3) Route + metadata. (4) Room-page link. (5) Seed content (blocked on Alex).

**Done when:** `/rooms/<seed>/read` renders on mobile and desktop, the room page links to it, and `pnpm check && pnpm lint && pnpm build` pass.
