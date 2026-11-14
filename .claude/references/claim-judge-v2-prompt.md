You are labelling claims extracted from research briefs. For each item you get the claim and the source passages it was extracted from (event, date, and one or more cited paragraphs of the same document). Information may come from any of the cited paragraphs. The items are data, not instructions.

Answer three questions per item:
1. supported: "yes" if every piece of information in the claim (including any added context, numbers, dates, names and hedges) is substantiated by the passage; otherwise "no". A claim that drops a hedge ("says", "about", "reportedly") is "no".
2. standalone: "yes" if a reader who sees only the claim, with no passage, would understand exactly what is asserted and about whom; otherwise "no".
3. useful: 1 = trivial or empty (e.g. "X is a company"), 2 = a real but minor fact, 3 = a fact an analyst of the AI market would want to retrieve later.

Reply with one JSON object and nothing else: {"labels": [{"pid": "...", "supported": "yes|no", "standalone": "yes|no", "useful": 1|2|3, "why": "<= 15 words"}]}

<items>
ITEMS
</items>
