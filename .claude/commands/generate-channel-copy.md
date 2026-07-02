---
name: generate-channel-copy
description: "Channel-ready copy variations (email/ads/social/landing) with A/B variants + QA checklist. Use when you have a messaging brief and need the actual drafts per channel."
argument-hint: "[channels + persona + offer, e.g. 'email,linkedin, CIO, data platform']"
---

# Command: generate-channel-copy

## Inputs
- **channels** – comma-separated list (email, ads, social, landing, sms, in-app).
- **persona** – target audience/persona.
- **offer** – product/feature/value prop.
- **tone** – optional tone descriptor (bold, trusted, playful, technical).
- **length** – optional length constraint (short, medium, long, character count).

## Workflow
1. **Brief Mapping** – align persona + offer to message architecture.
2. **Hook Generation** – produce multiple hooks per channel.
3. **Body Copy Draft** – craft channel-specific copy with personalization tokens and proof points.
4. **CTA Alignment** – suggest primary/secondary CTAs plus urgency modifiers.
5. **QA Checklist** – highlight compliance, accessibility, localization considerations.

## Outputs
- Copy deck table (channel, hook, body, CTA, notes).
- Variant suggestions for A/B testing.
- QA checklist (links, tokens, tone reminders).

## Agent/Skill Invocations
- `conversion-copywriter` – drafts copy.
- `voice-editor` – enforces tone + compliance.
- `voice-guidelines` skill – supplies do/don't examples.

---
