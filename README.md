# msabanluc.github.io

Personal academic website of **Michael T. Saban**, Computer Science PhD student at Loyola University Chicago.
Live at <https://msabanluc.github.io>.

Built from the [al-folio](https://github.com/alshedivat/al-folio) Jekyll template (v1.x). Theme runtime lives in the
`al-*` gems pinned in `Gemfile`; see [`AGENTS.md`](AGENTS.md) and [`docs/`](docs/) for how the template is put together.

## Where things live

| What                     | Where                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------- |
| Bio, profile photo       | `_pages/about.md`, `assets/img/prof_pic.jpg`                                           |
| Social links             | `_data/socials.yml`                                                                    |
| Site title, SEO metadata | `_config.yml` (top section)                                                            |
| Publications             | `_bibliography/papers.bib` (shared with the CV; new DOIs arrive via the ORCID sync PR) |
| News items               | `_news/`                                                                               |
| Blog (paper reviews)     | `_posts/`, started from `_templates/paper-review.md`                                   |
| CV (LaTeX)               | `cv/`; see [`cv/README.md`](cv/README.md)                                              |

## Writing a paper review

```bash
bin/new-paper-review "Short paper title"   # in Git Bash; creates _posts/YYYY-MM-DD-short-paper-title.md
```

Fill in the sections, pick 1-3 tags from the list in the front matter, and preview before pushing.

## Local preview (Docker)

```powershell
docker compose up        # first run builds the image; then open http://localhost:8080
docker compose down      # stop
```

Edits to content are picked up automatically; refresh the browser. After editing `_config.yml`, run `docker compose restart`
(the container's config watcher does not see edits made from Windows).

## Automation

| Workflow                | When                 | What it does                                                            |
| ----------------------- | -------------------- | ----------------------------------------------------------------------- |
| `deploy.yml`            | push to `main`       | Builds the CV PDF from `cv/`, builds the site, publishes to `gh-pages`. |
| `orcid-sync.yml`        | Mondays, or manually | Opens a PR adding ORCID works whose DOI is not yet in `papers.bib`.     |
| `broken-links-site.yml` | after each deploy    | Checks internal links in the built site.                                |
| `prettier.yml`          | push / PR            | Formatting check (`npx prettier . --write` fixes).                      |
| `codeql.yml`            | push / PR / weekly   | Code scanning, including the workflows themselves.                      |
| `upgrade-check.yml`     | config changes       | `al-folio upgrade audit` for template upgrades.                         |
| `axe.yml`               | manual               | Accessibility check.                                                    |

`orcid-sync.yml` needs one repository setting: **Settings → Actions → General → Workflow permissions → Allow GitHub
Actions to create and approve pull requests**.

## License

Site code: MIT (see [`LICENSE`](LICENSE), from al-folio). Content: © Michael T. Saban.
