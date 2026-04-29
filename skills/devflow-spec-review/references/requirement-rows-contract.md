# Requirement Rows Review Excerpt

Spec review checks that every core row has ID, Statement, Acceptance, Priority, Source / Trace Anchor, and Component Impact or Affected Components as appropriate.

- Statement should use EARS-style structure and avoid ambiguous actors, hidden timing, and untestable wording.
- Acceptance should be BDD-like Given / When / Then and independently judgeable.
- Source must point to IR / SR / AR / meeting note / owner decision, not an undocumented memory.
- SR rows use Affected Components; AR / DTS / CHANGE rows use Component Impact.
- Missing business fact is USER-INPUT; wording/structure gaps are usually LLM-FIXABLE; component boundary decisions are TEAM-EXPERT.
