# Working notes for the CV repo

- The `.tex` sources double as a git-tracked record of everything JF has done.
  Never delete entries or their descriptions: comment them out (`%`) instead, so the history stays in the source.
- `sections/publications.tex` is generated from ADS by `scripts/build_cv_pubs.py`; run it in the `cv` mamba environment (`mamba run -n cv python scripts/build_cv_pubs.py`), which has the `ads` package, with the token in `~/.ads/dev_key`.
  All settings (section overrides, `hide`, `contributions`, `highlight`, `unpublished`) live in `scripts/pubs_config.yaml`, so a rerun reproduces them; hand edits to `publications.tex` are overwritten.
  In that YAML, keep LaTeX out of double-quoted strings (backslashes are escapes there).
- The "At a glance" line in `sections/summary.tex` updates itself.
  Publication statistics come from `sections/pubstats.tex`, which `build_cv_pubs.py` writes.
  The funding and invited-talk totals are counted from the `\grant` and `\talk` entries and saved to the `.aux` file, so they need a second compile (shown as ?? until then).
  Write new grants as `\grant{amount}{name}{dates}` (counted) or `\grant*{...}` (listed, not counted), and new invited talks as `\talk` instead of `\item`.
- The general CV (`main`) is 11 pt with the publication list after Fellowships/Honors.
  Application-specific versions live on their own branches: `hubble-2026` (12 pt, NHFP font rule; publication list on its own page with restarted numbering so it can be uploaded separately; teaching and outreach ahead of observing and software).
- LaTeX and Markdown: one sentence per line.
- Do not commit or push; JF reviews and commits. The repo syncs with Overleaf.
