# LinkedIn draft — paper-trail-ph (deslopped, final)

Deslopped 2026-07-04: deterministic oracle CLEAN, voice + fact/guardrail checkers passed (2 rounds). Post the link in the FIRST COMMENT, never the body.

## Post body

The flood-control scandal has a new name in it almost every week. Blacklisted contractors in February. A senator's arrest warrant in June. A plunder charge this month. Each story names one contractor or one official. Then the trail goes cold, because the records that would connect them sit in separate government systems that do not talk to each other.

So I connected them. paper-trail-ph is an open graph of Philippine government accountability data. It pulls 248,220 DPWH infrastructure contracts, PHP 6.38 trillion across 11,161 contractors. Then it joins them to legislators, procurement records, and the cases already in the news.

Type a contractor's name and you see every district office it won work from, who it bid against, and how concentrated its wins are. Type a district office and you see which firms it keeps awarding to. The contractors named in this year's blacklist are already in the data, so their network shows up the moment you search.

It separates recorded fact from inference.
- Recorded facts (a contract award, a blacklist, a filed charge) are drawn solid, each linked to its public source.
- Inferred links (shared bidding, matching details) are drawn faint and labeled as inferred, never as proof.
- Every charge shows "case pending" with a link to the filing. Charges are allegations.

It flags patterns for review and links you to the record so you can check for yourself. It does not conclude anyone is guilty. A shared surname is not the same family. Concentration can have honest explanations.

Open it in a browser, no install. Code and data sources are open, built on the BetterGov.ph public datasets.

Link in the comments.

## First comment

[live site URL] plus the GitHub repo.

## Poster notes

- Hero is a native screen recording of the Topnotch-Catalyst search demo and the story-rail, uploaded as video, not a link.
- One repeatable number carries the post: PHP 6.38 trillion in DPWH contracts.
- Do not name an individual senator as the tool's verdict. The two Senate cases stay as anonymized news beats; named specifics live in the graph with their source links.
- Before posting, confirm COA finding nodes actually shipped. If COA stays Phase 2, the post already avoids claiming COA (the recorded-facts example is award, blacklist, filed charge).
