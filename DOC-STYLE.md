# DOC-STYLE: documentation rules for every repository in the estate

These rules apply to every Markdown document in every WyattAu repository:
READMEs, AGENTS.md files, design documents, runbooks, and ledgers.

## 1. Character rule: no em-dash

The em-dash character does not appear in any document. Use a colon, a
comma, a semicolon, or parentheses instead. The character carries no
meaning that those do not, and it renders inconsistently across
terminals and fonts.

Check any tree with:

```bash
grep -rn --include='*.md' '' .
```

The count must be zero. Wire the check into the repository's lint
workflow where a docs tree exists.

## 2. Register rule: technical, concise, non-handwavy

Every sentence in a document does exactly one of the following:

1. States a fact and cites where it is enforced or defined (file path,
   theorem name, test name, commit, or external link).
2. Gives a procedure (commands, in execution order, with expected
   output).
3. States a decision and its reason, with the rejected alternatives
   named.

Marketing adjectives do not appear in documentation. Performance
claims carry measured numbers and the measurement method. "Fast" is
not a claim; "P99 under 5 ms at 10k req/s, measured by criterion
commit `abc1234`" is.

## 3. Citation rule: unlinked claims are draft material

A claim that cannot cite its enforcement point or source is not
documentation; it is a TODO. The citation forms accepted in this
estate:

- Repository link: `[name](https://github.com/WyattAu/name)`.
- File path: `src/service/sending/sender.rs`.
- Theorem or test name: `take_conserves`, `fresh_chain_converges_with_boot_patches`.
- External source: author, title, year, link.
- Commit: short hash plus one-line subject.

## 4. Sweep procedure for existing documents

```bash
grep -rln --include='*.md' '' . | while read -r f; do
  sed -i 's/: /: /g; s///g' "$f"
done
```

Review the diff before committing: the replacement is mechanical and
the surrounding sentence must still read correctly.
