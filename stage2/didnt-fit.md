# Didn't fit the standard — <account>

<!-- Template for work/didnt-fit/<account>.md, written by the mapper from the extractors' section K
plus its own findings. graph.py merges every account's file into out/DIDNT-FIT.md, ranked by how often
the same problem came up, with doc ids as proof. One row per problem; the same problem on several
documents is one row with all the doc ids. Types: missing_field / family_misfire / no_family_fits /
missing_edge / missing_allowed_value / other. -->

| type | what did not fit | which DCG place | docs (proof) | suggested change (for the user to decide) |
| --- | --- | --- | --- | --- |
| missing_allowed_value | execution status: signed by one side only, or unsigned draft | `status` in dcg/properties.csv has signed / deemed / notified … but no one-sided or unsigned value | doc 004, doc 006 | add `signed_one_side`, `unsigned` to `status`, or a separate `execution` property |
| missing_field | … | … | … | … |

## Family notes

<!-- Where a tree matched a family only loosely (family_misfire) or none (no_family_fits): the tree,
the shape found (node types and edges present), the nearest family and what test it failed. -->

## Anything else the extractors flagged

<!-- Section J notes that name a DCG gap but do not fit a row above. -->
