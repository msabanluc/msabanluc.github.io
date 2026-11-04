#!/usr/bin/env python3
"""Append works from an ORCID record to a BibTeX file, matched by DOI.

For every work on the public ORCID record that has a DOI not already present in
the bib file, fetch BibTeX from doi.org (content negotiation), tidy it, and
append it. Existing entries are never touched, so hand edits (selected, pdf,
preview, abbr, ...) survive. Works without a DOI are only reported; add those by
hand.

Standard library only. Usage:

    python3 bin/orcid_sync.py --orcid 0009-0002-8031-4669 \
        --bib _bibliography/papers.bib --summary /tmp/summary.md

Exit status is 0 whether or not anything was added; failures to fetch a DOI are
listed in the summary. A non-zero exit means ORCID itself could not be read.
"""

import argparse
import datetime
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

USER_AGENT = "msabanluc.github.io orcid-sync (mailto:msaban@luc.edu)"

# Crossref sometimes lists the owner without the middle initial; the site and CV
# use one consistent form so jekyll-scholar and biblatex can highlight it.
OWNER_NAME = re.compile(r"\bSaban,\s*Michael(?:\s+T\.?)?(?=\s+and\b|$)")
OWNER_CANONICAL = "Saban, Michael T."

# Fields holding URLs or identifiers, which must not be LaTeX-escaped.
VERBATIM_FIELDS = {"doi", "url", "html", "pdf", "issn", "isbn"}

# Order of fields in written entries; anything else follows alphabetically.
FIELD_ORDER = [
    "abbr", "bibtex_show", "keywords", "title", "author", "editor", "journal", "booktitle",
    "volume", "number", "pages", "year", "month", "address", "publisher", "doi", "html",
]

# Fields from doi.org that add nothing on the site or CV.
DROP_FIELDS = {"url", "collection"}

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

TITLE_STOPWORDS = {"a", "an", "the", "of", "on", "in", "for", "and", "to", "with", "at", "by", "from", "abstract"}


def http_get(url, accept, retries=3):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            if err.code == 404 or attempt == retries:
                raise
        except urllib.error.URLError:
            if attempt == retries:
                raise
        time.sleep(2 * attempt)


def normalize_doi(doi):
    doi = doi.strip().lower()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi)


def orcid_works(orcid):
    """Return (dois, no_doi_titles) for the public works on an ORCID record."""
    data = json.loads(http_get(f"https://pub.orcid.org/v3.0/{orcid}/works", "application/json"))
    dois, no_doi = [], []
    for group in data.get("group", []):
        ids = (group.get("external-ids") or {}).get("external-id") or []
        group_dois = [
            normalize_doi(i["external-id-value"])
            for i in ids
            if i.get("external-id-type") == "doi" and i.get("external-id-relationship", "self") == "self"
        ]
        if group_dois:
            dois.append(group_dois[0])
        else:
            summary = group["work-summary"][0]
            no_doi.append(summary["title"]["title"]["value"])
    return dois, no_doi


def existing_dois_and_keys(bib_text):
    dois = {normalize_doi(m) for m in re.findall(r"^\s*doi\s*=\s*[{\"]([^}\"]+)[}\"]", bib_text, re.I | re.M)}
    keys = set(re.findall(r"^@\w+\s*\{\s*([^,\s]+)\s*,", bib_text, re.M))
    return dois, keys


def parse_bibtex(text):
    """Parse a single BibTeX entry into (entry_type, fields). Values keep inner braces."""
    m = re.search(r"@(\w+)\s*\{\s*[^,]*,", text)
    if not m:
        raise ValueError("no BibTeX entry found")
    entry_type, pos, fields = m.group(1).lower(), m.end(), {}
    while True:
        m = re.compile(r"\s*([A-Za-z_][\w-]*)\s*=\s*").match(text, pos)
        if not m:
            break
        name, pos = m.group(1).lower(), m.end()
        if text[pos] == "{":
            depth, start = 0, pos
            while True:
                if text[pos] == "{":
                    depth += 1
                elif text[pos] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                pos += 1
            value, pos = text[start + 1 : pos], pos + 1
        elif text[pos] == '"':
            end = text.index('"', pos + 1)
            value, pos = text[pos + 1 : end], end + 1
        else:
            m = re.compile(r"[^,}\s]+").match(text, pos)
            value, pos = m.group(0), m.end()
        fields[name] = value.strip()
        m = re.compile(r"\s*,?").match(text, pos)
        pos = m.end()
    return entry_type, fields


def escape_latex(value):
    # Escape bare specials; leave already-escaped ones alone.
    return re.sub(r"(?<!\\)([_&%#])", r"\\\1", value)


def ascii_slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def make_key(fields, taken):
    first_author = fields.get("author", "anon").split(" and ")[0]
    family = first_author.split(",")[0] if "," in first_author else first_author.split()[-1]
    words = [ascii_slug(w) for w in re.sub(r"[{}]", "", fields.get("title", "")).split()]
    word = next((w for w in words if w and w not in TITLE_STOPWORDS and not w.isdigit()), "")
    base = f"{ascii_slug(family) or 'anon'}{fields.get('year', '')}{word}"
    key, suffix = base, ord("a")
    while key in taken:
        key, suffix = f"{base}{chr(suffix)}", suffix + 1
    return key


def tidy(entry_type, fields, doi):
    fields = {k: v for k, v in fields.items() if k not in DROP_FIELDS}
    if "title" in fields:
        title = re.sub(r"</?(?:i|b|em|strong|sub|sup|scp|span)\b[^>]*>", "", fields["title"])  # Crossref markup
        fields["title"] = re.sub(r"^Abstract\s+\w+:\s*", "", title)
    if "author" in fields:
        fields["author"] = OWNER_NAME.sub(OWNER_CANONICAL, fields["author"])
    if "pages" in fields:
        fields["pages"] = re.sub(r"\s*[–—-]+\s*", "--", fields["pages"])
    if "month" in fields:
        month = fields["month"].strip("{}").lower()[:3]
        if month in MONTHS:
            fields["month"] = month  # written bare, as a BibTeX month macro
        elif month.isdigit() and 1 <= int(month) <= 12:
            fields["month"] = MONTHS[int(month) - 1]
        else:
            del fields["month"]
    for name, value in fields.items():
        if name not in VERBATIM_FIELDS and name != "month":
            fields[name] = escape_latex(value)
    if re.search(r"suppl", fields.get("number", ""), re.I):
        fields["keywords"] = "abstract"  # conference abstract in a journal supplement
    fields["doi"] = doi
    fields["html"] = f"https://doi.org/{doi}"
    fields["bibtex_show"] = "true"
    return entry_type, fields


def format_entry(entry_type, key, fields):
    names = [n for n in FIELD_ORDER if n in fields] + sorted(n for n in fields if n not in FIELD_ORDER)
    width = max(len(n) for n in names)
    lines = []
    for n in names:
        value = fields[n] if n == "month" else "{" + fields[n] + "}"
        lines.append(f"  {n.ljust(width)} = {value}")
    return f"@{entry_type}{{{key},\n" + ",\n".join(lines) + "\n}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--orcid", required=True)
    parser.add_argument("--bib", required=True, help="BibTeX file to append to")
    parser.add_argument("--summary", help="write a Markdown summary (used as the PR body)")
    parser.add_argument("--dry-run", action="store_true", help="print new entries instead of appending")
    args = parser.parse_args()

    with open(args.bib, encoding="utf-8") as f:
        bib_text = f.read()
    have_dois, taken_keys = existing_dois_and_keys(bib_text)

    try:
        orcid_dois, no_doi = orcid_works(args.orcid)
    except (urllib.error.URLError, ValueError, KeyError) as err:
        print(f"error: could not read ORCID record {args.orcid}: {err}", file=sys.stderr)
        return 1

    new_entries, added, failed = [], [], []
    for doi in orcid_dois:
        if doi in have_dois:
            continue
        try:
            raw = http_get(f"https://doi.org/{doi}", "application/x-bibtex; charset=utf-8")
            entry_type, fields = tidy(*parse_bibtex(raw), doi)
        except (urllib.error.URLError, ValueError, IndexError, AttributeError) as err:
            failed.append((doi, str(err)))
            continue
        key = make_key(fields, taken_keys)
        taken_keys.add(key)
        have_dois.add(doi)
        new_entries.append(format_entry(entry_type, key, fields))
        added.append((key, doi, re.sub(r"[{}\\]", "", fields.get("title", ""))))

    if new_entries:
        if args.dry_run:
            print("\n".join(new_entries))
        else:
            stamp = datetime.date.today().isoformat()
            with open(args.bib, "a", encoding="utf-8", newline="\n") as f:
                if not bib_text.endswith("\n"):
                    f.write("\n")
                f.write(f"\n% Added from ORCID on {stamp}. Review, then add abbr / selected / pdf / preview as needed.\n\n")
                f.write("\n".join(new_entries))

    lines = [f"ORCID record [{args.orcid}](https://orcid.org/{args.orcid}): {len(orcid_dois)} works with a DOI, "
             f"{len(no_doi)} without.", ""]
    if added:
        lines += ["### Added to `" + args.bib + "`", ""]
        lines += [f"- `{key}`: {title} ([doi:{doi}](https://doi.org/{doi}))" for key, doi, title in added]
        lines += ["", "Check author names and titles, then set `abbr`, `selected`, `pdf`, or `preview` if wanted. "
                  "Entries with `keywords = {abstract}` were detected as journal-supplement abstracts.", ""]
    else:
        lines += ["No new DOIs.", ""]
    if failed:
        lines += ["### Could not fetch BibTeX", ""]
        lines += [f"- {doi}: {err}" for doi, err in failed] + [""]
    if no_doi:
        lines += ["### On ORCID without a DOI (add by hand if missing)", ""]
        lines += [f"- {t}" for t in no_doi] + [""]
    summary = "\n".join(lines)
    print(summary)
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
