# templates-lock - gene2-demo-shop

Records which `.github/templates/` version was vendored into `tests/_lib/`. On a repeat run, if a
vendored file is behind the current template, the audit notes it; update only with confirmation.
Checked byte for byte against the templates on 2026-09-23 (after the v3.1 template changes).

| Vendored path | Source | Vendored on | Template version |
|---|---|---|---|
| `tests/_lib/pages/*` | `.github/templates/pages/*` | 2026-09-23 | v3.1.0 (identical) |
| `tests/_lib/components/*` | `.github/templates/components/*` | 2026-09-23 | v3.1.0 (identical) |
| `tests/_lib/flows/*` | `.github/templates/flows/*` | 2026-09-23 | v3.1.0 (identical; `auth_flow` constants `USERNAME_INPUT` / `PASSWORD_INPUT` / `SUBMIT_BTN`) |
| `tests/conftest.py` | `.github/templates/conftest.template.py` | 2026-09-23 | v3.1.0 (identical: `--base-url` > `GENE2_BASE_URL` > config; `_looks_like_drift`; no heal context for `@pytest.mark.bug`) |
| `pytest.ini` | `.github/templates/pytest.ini.template` | 2026-09-23 | v3.1.0 ({level} -> functional) |
| `requirements.txt` | `.github/templates/requirements.template.txt` | 2026-09-23 | v3.1.0 (identical) |

`tests/_lib/__init__.py` is an empty package marker with no template.
