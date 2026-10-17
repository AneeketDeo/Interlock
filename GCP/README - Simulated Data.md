# RCA simulated data (seed 42)

Run: `python3 generate_data.py --out out` (stdlib only, deterministic).

- `out/data/*.csv`: one file per ontology class (node tables) plus `edges_*.csv` (relationships). Foreign keys (e.g. `machine_id`, `lot_id`) carry the remaining one-to-many links.
- `out/ground_truth.json`: planted cause, decoys, red herrings, blast radius, impact inputs, expected remediation, and agent test cases. Do not expose it to the agent.
- All timestamps are UTC ISO-8601. Data cut-off 2026-10-15 07:00Z; incident detected 07:15Z.

Planted scenario: LOT-409 (Tier-3 SUP-T3-01, hardness/carbon/Mn at the upper spec edge) plus CREW-B's rushed-handover calibration on 2026-10-14 that skipped step 6 (thermal offset verification) produce about 12 points of extra scrap on M02, M03, M06, M09, M11. Each factor alone is harmless (see `must_not_conclude`).

Deviations from the ontology list: no per-unit ProductUnit (scrap and yield are aggregated per work order and inspection); Cause, Decision, Approval and CorrectiveAction are populated only for the two historical incidents. The open incident has no cause, decision or approval yet, because the agent creates them. Mill certificate PDFs are referenced by `document_ref` but not generated.
