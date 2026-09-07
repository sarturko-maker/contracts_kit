# Topics — section I of the form (off by default)

Section I is filled only when `/extract` is run with `--topics`. Each ticked topic gets one entry per
part where it appears: `{topic, part, page_or_clause, words, reading}`. `words` are the exact words,
forty or fewer. `reading` is one of the fixed readings below and nothing else; when the words do not
fit any reading, use the closest and record the words in section J. `silent` means the document says
nothing on the topic.

| topic | fixed readings | note |
| --- | --- | --- |
| `freight` | `charged_at_cost` / `charged_basis_unspecified` / `charged_with_margin` / `included_in_price` / `customer_arranges` / `silent` | "may charge the cost of freight" = charged_at_cost; "freight shall be charged" with no basis = charged_basis_unspecified |
| `pricing` | `fixed_prices` / `price_list_referenced` / `cost_plus` / `silent` | a price list "issued separately" is price_list_referenced |
| `payment_terms` | `<n> days` (say from what: invoice date or end of month) / `silent` | write `30 days from end of month of invoice` |
| `termination_for_convenience` | `yes (<period>)` / `no` | a rolling agreement "terminable on six months' notice" is `yes (6 months)`; a fixed term with no convenience right is `no` |

Add a topic only when the business asks about it by name; add it here with its fixed readings, never
in the form. DCG: each entry becomes an L3 `term_fact` under a `clause` node (`has_clause`, `has_term`);
SALI classification left `pending`.
