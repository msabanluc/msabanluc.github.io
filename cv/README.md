# CV

Michael T. Saban's CV in [moderncv](https://ctan.org/pkg/moderncv) LaTeX. The structure follows
[gkthiruvathukal/cv](https://github.com/gkthiruvathukal/cv), except that the bibliography comes from ORCID through
`_bibliography/papers.bib` rather than from Zotero.

## Layout

| File                          | What it holds                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------- |
| `saban-cv.tex`                | Main file: personal data and section order.                                       |
| `settings.tex`                | moderncv style, spacing macros, and biblatex setup (drivers, filters, bold name). |
| `sections/*.tex`              | One file per CV section, hand-edited.                                             |
| `pending.bib`                 | Hand-maintained: manuscripts under review and in preparation.                     |
| `../_bibliography/papers.bib` | Published work, shared with the website and appended to by the ORCID sync action. |
| `private.tex`                 | Optional and gitignored. Private details (phone) for a local-only build.          |

## How publications are sorted

`sections/30-publications.tex` prints five subsections from the two bib files:

| Subsection                        | Rule                                                   | Order                  |
| --------------------------------- | ------------------------------------------------------ | ---------------------- |
| Peer-Reviewed Journal Articles    | `@article` without `keywords = {abstract}`             | newest first           |
| Conference & Workshop Papers      | `@inproceedings` / `@incollection` without the keyword | newest first           |
| Published Abstracts & Proceedings | `keywords = {abstract}`, any type                      | newest first           |
| Manuscripts Under Review          | `keywords = {underreview}` (in `pending.bib`)          | newest first           |
| Manuscripts In Preparation        | `keywords = {inprep}` (in `pending.bib`)               | order in `pending.bib` |

An entry of any other type (e.g. `@misc`) without one of these keywords is not printed. Give it a keyword or change its type.

When a paper is accepted: delete it from `pending.bib`, add it to ORCID, and the weekly ORCID sync opens a PR adding it to
`papers.bib`. (Add it to `papers.bib` by hand if it has no DOI.)

## Builds

**On GitHub.** The `cv` job in `.github/workflows/deploy.yml` compiles this folder on every deploy and publishes the PDF at
`/assets/pdf/michael-t-saban-cv.pdf`, which the site's CV page embeds. The PDF is never committed. That job fails if
`private.tex` is committed or if any `.tex` file here contains `\phone`.

**Locally, with Docker** (from the repo root, in PowerShell):

```powershell
docker run --rm -v "${PWD}:/work" -w /work/cv texlive/texlive:latest latexmk -pdf saban-cv.tex
Copy-Item cv/saban-cv.pdf assets/pdf/michael-t-saban-cv.pdf
```

The first run downloads a large TeX Live image (several GB). Copying the PDF into `assets/pdf/` lets the local Jekyll
preview show it on the CV page; that file is gitignored.

**Private copy with your phone number.** Create `cv/private.tex` containing `\phone[mobile]{...}` and build locally.
Share that PDF directly; never commit it or the file.

**Overleaf.** Upload this folder plus `papers.bib`, and change the `\addbibresource{../_bibliography/papers.bib}` line in
`settings.tex` to the uploaded path. Overleaf's default compiler settings (pdfLaTeX + biber via latexmk) work as is.
