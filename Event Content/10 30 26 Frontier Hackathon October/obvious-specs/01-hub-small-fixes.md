# 01 · Hub small fixes (empire-state-hub) · Tier 1, volume

Next.js 16 / React 19 / Tailwind, pnpm. **Read `node_modules/next/dist/docs/` before writing any code. This Next version has breaking changes (see AGENTS.md).** Each item is independent: one PR each, run in parallel.
Verify every PR with `pnpm check && pnpm lint && pnpm build`.

## H1 · Branded 404
There is no `src/app/not-found.tsx`. Add one using the existing header/footer components and site tokens, with links to Home and /rooms.
**Done when:** an unknown URL renders the branded page, and the build passes.

## H2 · Page metadata: Home + About
`src/app/(public)/page.tsx` and `about/page.tsx` export no `metadata`. Add a `title` and `description` drawn only from copy already on each page.
**Done when:** both pages have unique titles, and no new claims are added.

## H3 · Page metadata: Work, Journal, Changelog
Same as H2 for `work/`, `journal/` and `changelog/`.

## H4 · Page metadata: Architecture, Build Arcs
Same as H2 for `architecture/` and `build-arcs/`.

## H5 · sitemap
Add `src/app/sitemap.ts` covering the static public routes plus every room slug from `getRooms()` (`src/lib/rooms.ts`). Exclude `/ops/*`.
**Done when:** `/sitemap.xml` lists all public routes and rooms, with no `/ops`.

## H6 · robots
Add `src/app/robots.ts` that allows all, disallows `/ops/`, and points to the sitemap.

## H7 · Skip-to-content link
Add a visually hidden skip link as the first focusable element in `src/app/(public)/layout.tsx`, targeting its `<main>` (add `id="main"` to it). It must be visible on keyboard focus.
**Done when:** Tab from page load reveals the link, and Enter moves focus to main.

## H8 · Event structured data on room pages
In `src/app/(public)/rooms/[slug]/page.tsx`, emit a JSON-LD `Event` (`name`, `startDate`, `location.name`, `performer` = speaker names) built **only** from fields already in `rooms.json`. Speakers carry name/title/company/LinkedIn only; add nothing else.
**Done when:** the JSON-LD validates, and `pnpm check` (the public-safe scan) passes.

## H9 · Default Open Graph image
Add a site-wide `opengraph-image` (static or generated) using the house tokens: dark base, acid green `#8FE83A` accent, "Empire State" wordmark text.
**Done when:** the home page `<head>` carries `og:image` and the build passes.
