# sach — the Vietnamese ebook toolset

`sach` (sách, "book" in Vietnamese) is a from-scratch fork of the Standard Ebooks
toolset, re-adapted for **Vietnamese book editing standards** and stripped of all
Standard Ebooks branding. It produces EPUB ebooks from Vietnamese-language
source text using the same rigorous "source folder → clean → build" workflow,
but with Vietnamese editorial conventions built in.

```
sach [-h,--help] [--color] [-p,--plain] [-v,--version] <COMMAND> [<ARGS> ...]
```

Run `sach help` for the full command list, or `sach <command> --help` for
command-specific options.

---

## What makes sach different from the toolset it was forked from

All of the changes live in `sach/vietnamese.py` (the single place that encodes
Vietnamese editorial rules) plus the call sites that use it:

- **Unicode normalisation (NFC).** Vietnamese (`quốc ngữ`) text is stored in
  precomposed NFC form. If a source file is decomposed (NFD) — common with
  hand-edited Vietnamese files — `sach typogrify` and `sach word-count`
  normalise it to NFC before processing, so tone marks are composed into single
  code points instead of splitting words.
- **No end-of-word hyphenation.** Vietnamese words are already space-separated
  syllables, and Vietnamese publishing practice does not hyphenate at line
  ends. `sach hyphenate` is therefore a no-op for Vietnamese (`vi`, `vi-VN`,
  …) rather than inserting soft hyphens.
- **Word counting.** `sach word-count` treats the space as the primary word
  boundary, which matches how Vietnamese words are written, and normalises to
  NFC first so decomposed marks don't inflate the count.
- **Quotation style.** Vietnamese uses the same double/single curly quotation
  marks (`“ ” ‘ ’`) as English, so no quote-style conversion is applied.
- **Neutral templates.** Book templates (cover SVG, titlepage, colophon,
  imprint, uncopyright) carry no publisher logo or branding; the colophon
  credits the producer rather than a branding house.

The underlying EPUB tooling (draft creation, cleaning, ToC/manifest/spine
builders, endnote handling, linting, packaging) is unchanged from upstream, so
the full Standard Ebooks-style production workflow still works.

---

## Installation

The project installs a `sach` command. From this repository:

```shell
# From the project root
pipx install .                      # installs the `sach` executable
# or editable, for development
pipx install --editable .
```

Or create a virtualenv in-tree:

```shell
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/sach --version
```

`sach -v` reports the version plus an `editable` marker when installed in
editable mode. (Requires Python ≥ 3.10.12; the same transitive dependencies as
the upstream toolset are used.)

---

## The production pipeline

The typical flow for turning raw Vietnamese text into a finished EPUB mirrors
the Standard Ebooks source-folder model. `create-draft` writes the skeleton
into the current directory:

```
mkdir lib && cd lib
sach create-draft -a "Tác giả" -t "Tựa đề" --white-label  # 1. skeleton in ./
sach create-draft -a "Nam Cao" -t "Sống mòn" --white-label -l vi  # ...and set the language
# …drop your chapters into lib/epub/text/*.xhtml… (see layout below)
sach clean            .   # 2. canonicalise + fix indentation/spacing
sach build-toc        .   # 3. generate the table of contents + landmarks
sach build --output-dir=dist .   # 4. package compatible + advanced EPUB
```

`create-draft -l/--language` wires the language into the skeleton: it becomes
the `dc:language`, the top-level `xml:lang` of every generated document (so you
don't have to fix `en-US`/`LANG` yourself), and for a Vietnamese code it also
keeps the English title-caser from mangling the book title — `Sống mòn` stays
`Sống mòn` instead of becoming `Sống Mòn`.

Notes:

- `--white-label` produces a skeleton with **no** publisher logo or branding
  boilerplate — use it unless you want the default template set.
- `sach build` produces both a plain and an `*_advanced.epub` (Kobo-compatible)
  output in the target directory.
- `sach build --check` additionally runs epubcheck (requires Java).
- With no Java available, validate structurally instead (zip integrity + XML
  well-formedness) — see *Validation* below.

The source-folder structure `lib/` is the Standard Ebooks layout (modern
draft, no `src/` wrapper): `mimetype`, `META-INF/container.xml`,
`epub/content.opf`, `epub/text/*.xhtml`, `epub/css/*.css`,
`epub/images/*`.

---

## Vietnamese editorial commands

These are the commands you will reach for most when editing Vietnamese text:

- `sach typogrify` — normalise Vietnamese to NFC, then apply typography rules
  (smart quotes, dashes, ellipses). `--no-quotes` skips the smart-quote pass.
- `sach hyphenate -l vi` — no-op for Vietnamese (see above); pass an English
  code like `-l en-US` to hyphenate other-language passages.
- `sach word-count` — count words (Vietnamese-aware), optionally `-c` to
  categorise length and `-x` to exclude boilerplate files (ToC, colophon…).
- `sach find-mismatched-diacritics` — find words used with and without
  diacritics inconsistently (e.g. `cafe` vs `café`).
- `sach find-unusual-characters` — find characters outside an expected range.
- `sach clean` — canonicalise markup and fix spacing/indentation.

English-centric commands that make little sense for Vietnamese still exist
for completeness but are not normally used on Vietnamese books. `titlecase` is
language-aware: pass `-l vi` (or any Vietnamese code) and it returns the title
in Vietnamese **sentence case** (`Sống mòn`, not `Sống Mòn`) instead of English
title case.

---

## Covers

`sach build-cover` draws a cover for a book from the book's own metadata —
nothing is AI-generated, and the same book always produces the same image.

```shell
sach build-cover -l "Tiểu thuyết" --overwrite lib   # writes lib/epub/images/cover.jpg
sach build-cover --list-themes                      # see the palettes
sach build-cover -t "Sống mòn" -a "Nam Cao" -o cover.jpg --theme paper
```

- The **palette** comes from `schema:genre` first, then `dc:subject` (English or
  Vietnamese words both work), and finally from a stable hash of the title, so a
  book with no genre metadata still gets a consistent cover of its own.
- The cover is a 1200×1800 JPEG: a themed ground, a ruled frame, the author, the
  title set in a Vietnamese-capable serif, and a genre label. `-s WIDTHxHEIGHT`
  changes the size; `--theme` forces a palette.
- Run it on a source folder to read the metadata, or pass `-t`/`-a` directly.
  Without `--overwrite` an existing cover is left alone.

---

## Validation without Java

If you can't run `sach build --check` (no Java/epubcheck), validate the built
EPUB yourself:

```shell
# zip integrity
unzip -t outdir/*.epub
# XML well-formedness of every file (example)
cd outdir
for f in $(unzip -Z1 *.epub | grep -E '\.(xhtml|opf|xml)$'); do
  unzip -p *.epub "$f" | python3 -c "import sys,xml.etree.ElementTree as ET; ET.fromstring(sys.stdin.buffer.read()); print('OK', '$f')"
done
```

Also re-check that every endnote reference in the chapters resolves to a note
in the endnotes file, and that the spine lists files in reading order.

For Vietnamese books, `sach lint` reports several English-centric rules as
false positives (titlecase, punctuation-in-italics, `<title>` format). Treat
those as informational; the language-agnostic rules (structure, metadata,
links, semantics) are what matter.

Most of them are now suppressed automatically: when an ebook's `<dc:language>`
is a Vietnamese code, `sach lint` compares headings and name titles against
Vietnamese sentence case instead of English title case, so the titlecase
warnings (`s-023`, `t-064`) stop firing for Vietnamese books. The remaining
English word that is hard to localise is the ToC's titlepage label, which the
toolset hardcodes as "Titlepage" (`m-045`); record a translation in a root
`se-lint-ignore.xml` if you want to replace it.

---

## Development

- Run the test suite: `.venv/bin/python -m pytest` (or the venv created by
  your package manager). The suite includes Vietnamese-specific tests in
  `tests/test_vietnamese.py`.
- `pylintrc` and `pyrightconfig.json` are configured for the `sach` package
  layout; install `pylint`/`pyright` + the typing stubs into the project venv,
  then run on `sach/`.

---

## Copyright & licensing

This is a fork of the Standard Ebooks toolset (GPLv3), re-released under the
same licence. The `sach/data/templates` are CC0. Third-party bundles in
`sach/vendor` and `sach/data` carry their own licences (see their directories).

The `sach` fork strips the Standard Ebooks brand, name, and logo but retains
the upstream's GPLv3 licence and its core codebase. When your *ebook content*
itself is a copyrighted translation or has a copyrighted editor's apparatus,
that copyright is separate from the toolset licence — check the book's own
rights before redistributing it.