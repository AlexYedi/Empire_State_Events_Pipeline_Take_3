---
name: sequence-architecture
description: "Design multi-step outbound sequences that convert. Timing, channel mix, variant strategy, and escalation logic for cold email campaigns."
---

# Sequence Architecture

## When to Use
- Building a new outbound campaign from scratch
- Restructuring sequences with poor step-2+ engagement
- Designing multi-channel cadences (email + LinkedIn + phone)
- Setting up A/B testing frameworks for sequence optimization

## Framework

### Sequence Design Principles

1. **Every step earns the next** — Step 1's job is to get Step 2 opened. Step 2's job is to get a reply. Never front-load everything into Step 1.
2. **New value every touch** — Each step must introduce a new angle, insight, or proof point. "Following up" is not a strategy.
3. **Decay is natural** — Open and reply rates drop with each step. Design for this: your best material goes in Steps 1-2, your boldest ask goes in the final step.
4. **Variants multiply learning** — Run 2-3 subject/body variants per step. At 200+ sends per variant, you have statistical significance.

---

### The 4-Step Core Sequence

This is the baseline architecture. Adapt timing and angles to your ICP.

| Step | Day | Channel | Objective | Angle Strategy |
|------|-----|---------|-----------|---------------|
| **1** | 0 | Email | Open + Reply | Lead with strongest signal or observation |
| **2** | 3-4 | Email | Reply | New value: resource, benchmark, or case study |
| **3** | 7-8 | Email | Reply or Referral | Social proof or creative ideas angle |
| **4** | 14 | Email | Close or Redirect | Breakup ("should I close this out?") or referral ask |

**Total campaign duration:** 14 days
**Total touches:** 4 emails

---

### Extended Sequence (Multi-Channel)

For high-value accounts or enterprise targets, layer in LinkedIn and phone:

| Step | Day | Channel | Objective |
|------|-----|---------|-----------|
| **1** | 0 | Email | Signal-based opening |
| **2** | 1 | LinkedIn | Connection request with personalized note |
| **3** | 3 | Email | New value angle |
| **4** | 5 | LinkedIn | Engage with their content (like/comment) |
| **5** | 7 | Email | Case study or social proof |
| **6** | 8 | Phone | "Following up on the email I sent" |
| **7** | 10 | LinkedIn | Direct message with resource |
| **8** | 14 | Email | Breakup or referral |

**Total campaign duration:** 14 days
**Total touches:** 8 (4 email + 3 LinkedIn + 1 phone)

---

### Variant Strategy

Every email step should have **2-3 variants** to enable testing:

| Variant Type | What You're Testing | Example |
|-------------|-------------------|---------|
| **Subject variants** | Which framing gets opens | A: `{{company}} outbound` vs B: `quick question` |
| **Opening variants** | Which personalization resonates | A: Signal-based vs B: Problem-based |
| **CTA variants** | Which ask gets replies | A: "Worth a look?" vs B: "Want me to send the playbook?" |
| **Angle variants** | Which value prop converts | A: ROI-focused vs B: Time-savings-focused |

**Testing rules:**
- Only test ONE variable per variant pair (subject OR body, not both)
- Minimum 200 sends per variant before drawing conclusions
- Winner = highest positive reply rate (not total reply rate — ignore "not interested" replies)
- Rotate winning variants into the "control" and test new challengers

---

### Timing Optimization

| Factor | Recommendation | Why |
|--------|---------------|-----|
| **Send days** | Tuesday-Thursday | Monday = inbox overload. Friday = checked out. |
| **Send window** | 8:00 AM - 11:00 AM prospect's timezone | Caught during morning email triage |
| **Step gaps** | 3-4 days between emails | Enough to not feel pushy, close enough to maintain context |
| **Reply window** | Check within 30 min of sends | Fast replies to "interested" responses 3x close rate |
| **Match lead ESP** | Enabled | Send from Gmail to Gmail, Outlook to Outlook — improves deliverability |

---

### Sequence Settings Checklist

Configure these before launching any campaign:

| Setting | Value | Reason |
|---------|-------|--------|
| **Stop on reply** | ON | Never email someone who already responded |
| **Stop on auto-reply** | OFF | Auto-replies (OOO) shouldn't kill the sequence |
| **Text only** | ON | HTML emails trigger spam filters more often |
| **Link tracking** | OFF | Tracking pixels and links hurt deliverability |
| **Open tracking** | OFF | Same — open tracking = invisible pixel = spam risk |
| **Daily send limit** | Per account limits | Respect your email provider's sending limits |
| **Email gap** | 10-20 minutes | Time between individual sends — avoids burst patterns |
| **Random delay** | 5-10 minutes | Adds randomness to look human |

---

### Escalation Logic

What happens when the standard sequence doesn't convert:

```
Standard Sequence (14 days)
    ↓ No reply
Wait 30 days
    ↓
Re-engagement Sequence (different angle, 3 steps)
    ↓ No reply
Wait 60 days
    ↓
Trigger-based Re-entry
    (Only re-enter if new signal detected: funding, hiring, tech change)
```

**Never:**
- Re-enroll someone in the same sequence
- Contact someone who explicitly said "not interested"
- Send more than 2 sequences to the same person in 6 months without a new signal

---

### Campaign Naming Convention

Use a consistent naming structure so performance data is analyzable:

```
{Client} - {Segment} - {Angle} - {Version}
```

Examples:
- `Acme - Enterprise VP Sales - Hiring Signal - v1`
- `Acme - SMB Founders - Referral Ceiling - v2`
- `Acme - Mid-Market Growth - Tech Stack Change - v1`

This makes it trivial to filter analytics by client, segment, or angle.

---

### Architecture Decision Tree

```
Is the target account high-value (>$50K ACV)?
├── YES → Extended Multi-Channel Sequence (8 touches, 14 days)
│         Layer email + LinkedIn + phone
│         Personalize every touch individually
│
└── NO → Standard 4-Step Email Sequence (4 touches, 14 days)
         Use signal-based personalization at scale
         Rely on variants for optimization

Is this a new persona/segment you haven't tested?
├── YES → Run 3 variants of Step 1 with 200+ sends each
│         Wait for data before building Steps 2-4
│
└── NO → Clone your best-performing sequence
         Swap personalization for new segment
         Keep winning structure intact
```

## Templates

### Campaign Launch Checklist
```
Pre-Launch:
- [ ] ICP and persona defined
- [ ] Lead list built and verified (bounce rate < 3%)
- [ ] Email accounts warmed (2+ weeks, 30+ emails/day)
- [ ] Sequence written (2-3 variants per step)
- [ ] Settings configured (tracking off, text-only, stop on reply)
- [ ] Naming convention applied
- [ ] Test send to yourself and team for QA

Post-Launch (Day 3):
- [ ] Check open rates (target: 60%+)
- [ ] Check bounce rate (must be < 3%)
- [ ] Check spam complaints (must be 0)
- [ ] Review any replies for pattern recognition

Post-Launch (Day 14):
- [ ] Calculate positive reply rate per variant
- [ ] Identify winning variants
- [ ] Document learnings
- [ ] Plan next iteration
```

## Tips
- Build your sequence backwards — write the breakup email first, then work back to Step 1. This forces you to think about the full arc.
- The best Step 2 is a reply to Step 1 (literally in the same thread), not a new email. This uses the "thread effect" for higher opens.
- Don't over-engineer your first sequence. Launch with 4 steps, 2 variants each, and iterate from data. Perfection before launch = wasted time.
- Keep a "swipe file" of every reply you get — positive and negative. The language prospects use to say "yes" and "no" is gold for future copy.
- If your open rate drops below 40% mid-campaign, stop sending. You have a deliverability problem, not a copy problem.

---

*Progressive disclosure: load channel-specific templates and industry playbooks only when building sequences for a specific campaign.*
