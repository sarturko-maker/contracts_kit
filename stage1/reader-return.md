# The reader's return line

After writing the two card files the reader returns exactly one line and nothing else:

```
doc 017 | <kind> | <them> ↔ <us> | <live/dead/unsure> | trade: <all/part/no/unsure> | parts: y/n | work/cards/017.md
```

- `<kind>`: the answer to question 1.
- `<them>`: their first signing entity as printed; `<us>`: our signing entity, or `not found`.
- `trade`: `all` for "all purchases"; `part` for a product set, a project, site or programme, or
  a period; `no` for "does not govern trade"; `unsure` for "can't tell".
- `parts`: `y` if question 5 is yes.

Example:

```
doc 001 | master or framework | Tallowfield Industries (North) Limited ↔ Marrowgate Supply Ltd | live | trade: all | parts: y | work/cards/001.md
```
