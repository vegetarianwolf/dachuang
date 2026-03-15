## Cursor Cloud specific instructions

### Project overview

This is "dachuang" (大创) — an academic research data pipeline from Nankai University that studies the relationship between government fiscal gaps and PE investment into SRDI (专精特新) enterprises in Chinese cities. It consists of standalone Python scripts (no web server, no CLI framework). All data is CSV-based (no database).

### Environment

- **Python 3.13** (pinned in `.python-version` and `pyproject.toml`)
- **Package manager:** `uv` — use `uv run python <script>.py` to run scripts
- **Core dependencies:** `pandas`, `numpy` (installed via `uv pip install`)
- **Proprietary dependencies (not installable without institutional credentials):**
  - `csmarapi` — CSMAR database API (Nankai University subscription, not on PyPI)
  - `ceic_api_client` — CEIC economic data API (requires paid token, custom index: `https://downloads.ceicdata.com/python`)
- **Data files:** stored in Git LFS under `cleaned_data/` and `csmar_data_export/`. Run `git lfs pull` if files show as LFS pointers.

### Running scripts

All scripts are standalone. Run with:
```
uv run python <script_name>.py
```

**Scripts that work without proprietary APIs** (use local CSV data only):
- `build_regression_panel.py` — builds the final regression dataset from cleaned CSVs
- `extract_srdi_samples.py` — marks and extracts SRDI investment samples
- `audit_regression_panel.py` — audits the final dataset (note: expects English column names but data uses Chinese names after `build_regression_panel.py` renames them)
- `clean_pe_data.py` — cleans PE investment event data (needs raw input CSVs in `清科政府引导基金投资事件截止到2024年/`)
- `clean_fiscal_data.py` — cleans CEIC fiscal data (needs raw CEIC CSVs)

**Scripts that require API credentials:**
- `main.py`, `download_csmar*.py`, `search_csmar.py` — need `csmarapi` + CSMAR login
- `download_ceic_fiscal_data.py`, `test_ceic*.py` — need `ceic_api_client` + token in `ceic_token.txt`

### Gotchas

- `pyproject.toml` has `dependencies = []` (empty). The actual runtime dependencies (`pandas`, `numpy`) must be installed manually via `uv pip install pandas numpy`.
- There are no automated tests, linter config, or CI/CD in this project.
- The `audit_regression_panel.py` script will error because `build_regression_panel.py` renames columns to Chinese but the audit script expects English names like `City`, `Year`.
