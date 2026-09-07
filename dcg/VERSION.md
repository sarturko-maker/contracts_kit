# DCG files in this folder

Copied, unchanged, from https://github.com/sarturko-maker/Contract_graph

- Standard version: DCG v0.1.0 (from the repository README)
- Commit: 24cb79e96e1ef17ef5ca200f39e6104a2f5c4582
- Commit date: 2026-08-23
- Copied on: 2026-09-06

| File | What it is |
| --- | --- |
| node_types.csv | 29 node types by layer |
| edge_types.csv | 60 edge types with direction rules and time properties |
| properties.csv | 28 properties with allowed values |
| aliases.csv | 367 cover-page titles mapped to node types and family hints |
| families.csv | 36 families (13 customer, 12 supplier, 11 vendor) plus the C0, S0, V0 catch-all rows, each with its structural test |
| overlays.csv | the 6 overlays (O1 security to O6 data protection) that cut across every family |
| sample-nodes-header.csv | header row of the standard's sample nodes.csv (neo4j-admin import convention) |
| sample-edges-header.csv | header row of the standard's sample edges.csv |

Rules: use these names verbatim; never invent DCG fields; where the form needs something DCG
lacks, write `DCG: none — didn't-fit candidate`. Do not change these files during a run.
