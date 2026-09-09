# Sorting rules

Two sets of rules, applied in this order: first every document is matched to an account
(section A, used by `/sort`); then, within an account, every document is given a status folder
(section B, used by the judge). Both are followed word for word.

## A. Sorting into account folders

> You are matching documents to the accounts in the ERP record. You have the account names, the
> company names from every sort card, and our own entity names (`inputs/our-entities.csv`, if
> present). You know how company groups, brands and old names fit together; use that. Two rules
> only:
>
> 1. The ERP record is the only source of folder names. One folder per account row, spelled
>    exactly as the row, under `out/<side>/`. Never create a folder from a name you found in a
>    document. Rows that are streams of one account share the main row's folder unless a
>    document names the stream; say which rows you treated as one.
> 2. Every match gets a basis and a confidence, written down. Basis is one of: `same name`,
>    `in the document` (the document itself says "a subsidiary of", "formerly known as", lists
>    the group companies, or shares a registered address or number with a company already
>    matched), or `known group` (you know the company belongs to the account's group but nothing
>    in the document says so; say what you know). Confidence is sure / fairly sure / not sure.
>    `known group` is never better than fairly sure, because the graph will need that link
>    evidenced or confirmed by a person.
>
> A document naming companies from more than one account is copied into every matching folder
> and marked shared. A document whose companies match no account goes to `_not-on-the-list`; one
> where you have a candidate but are not sure goes to `_not-sure`; one with no readable company
> name goes to `_no-name-found`. Inside the holding folders, group by the company name found, so
> the user decides once per name, not once per document. Where the file sat in the old
> repository is a clue, not a rule; if it disagrees with you, say so.
>
> Copy, never move. Write one line per document to `work/logs/sort.csv`: number, original path,
> company names found, account chosen, basis, confidence, note. Append every new company-name to
> account decision to `inputs/entity-map.csv` with `decided_by` = `claude`. The user edits that
> file (their rows say `decided_by` = `user` and win); `sort.py` replays it, so a re-run after
> edits does not ask you again. Tell the user which names need their decision.

## B. Sorting into status folders

> Within an account, decide each document's folder in this order and stop at the first rule
> that applies. Decide after linking: an amendment takes the status of the document it amends,
> and a document extended, terminated or replaced by another gets its status from that link. A
> credit application or an order confirmation that carries standard terms is judged by those
> terms like any other document, not by its title.
>
> 1. `6-business-practice`: internal playbooks or guidance about how the account is traded
>    (margin, pricing mechanics, market basket, what goes ad hoc). Not a contract; kept apart,
>    shown apart in the note.
> 2. `5-orders-drafts-duplicates`: single transactions (a purchase order, a quote, an order
>    confirmation without standard terms); an unsigned draft where a signed version of the same
>    document is in the pile; duplicates (the best copy is filed by the rules below, the others
>    here, marked "duplicate of"). Documents that belong to another account are filing errors:
>    note them and tell the main session.
> 3. `unsure`: no dates readable; signature page missing so signing is unknown; an unsigned
>    draft with no signed version in the pile ("draft, no signed copy found"); two candidates
>    for the same job and nothing on paper to choose between them.
> 4. `4-not-live`: end date passed and nothing extended it; terminated; replaced by a later
>    document in the pile; every part dead. A rolling or evergreen agreement is current unless
>    something in the pile records its end; the absence of later evidence does not end it.
> 5. `3-live-not-trade`: in force but does not govern trade: NDA, guarantee, data terms, code of
>    conduct, EDI terms; pricing, rebate, bonus and incentive letters that vary the commercials
>    of terms that govern elsewhere; notice letters.
> 6. `1-governs-trade`: live, governs trade, and its scope is all purchases between the parties
>    or as good as (a defined product set that looks like everything the account buys, or wording
>    that puts all orders under it). Its amendments, adoption agreements and schedules go with
>    it. If two documents both qualify for the same scope, both go here and the note says which
>    you would rely on and why, or "unresolved". If the only live trade-governing document has
>    a scope that reads as limited, it still goes here, with "scope on paper: …; confirm this is
>    all the trade" in the note.
>    A pricing or rebate letter that sets only prices or a period does not qualify under this
>    rule: it goes to `3-live-not-trade`, beside the agreement whose commercials it varies.
> 7. `2-governs-part-of-trade`: live, governs trade, but only for a project, site, programme or
>    named division, or a defined product set that is plainly not everything, while trade
>    outside that limit runs, or could run, under something else.
>
> A layered document is filed by its live parts; the note says which parts are dead. Every
> document goes in exactly one status folder; its tree number in the filename keeps the members
> of a tree together. Every document gets one line in the position note and one row in the
> document list, whatever folder it went to.
