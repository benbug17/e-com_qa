# Test Strategy (STLC mapped to this repo)
| STLC phase | Where it lives |
|---|---|
| Requirement analysis | Features in `tests/bdd/features/*.feature` (Gherkin acceptance criteria) |
| Test planning | Markers in `pytest.ini`: smoke, regression, negative, api, ui, db, e2e, bdd |
| Test design | Page Objects (`pages/`), data-driven CSV (`tests/data/`), JSON schemas (`utils/schemas.py`) |
| Environment setup | `docker-compose.yml`, `shop_app/seed.py`, autouse `clean_state` fixture |
| Execution | `pytest -m smoke` on every commit, `-m regression` nightly (Jenkinsfile `SUITE` param) |
| Defect tracking | `docs/defect_report_template.md`, failure screenshots, JUnit + HTML reports |
| Closure | Archived Jenkins artifacts, pass/fail trend |

SDLC fit: smoke gates every merge (CI), regression gates release, defects loop back to dev via the Fixed -> Retest flow.
