# E-Commerce Quality Automation Framework
Python · Selenium · Pytest · Page Object Model · Requests/Postman · PostgreSQL · pytest-bdd · Jenkins · Git

Includes a small demo shop (`shop_app/`: Flask + PostgreSQL) as the system under test.

## Layout
```
shop_app/   demo app (UI + REST API) + schema.sql + seed.py
pages/      Page Object Model (login, products, cart)
utils/      api_client, db helper, JSON schemas
tests/ui    Selenium: smoke / regression / negative
tests/api   REST: auth, products, orders, schema, data-driven (CSV)
tests/db    constraints, hashing, integrity (SQL)
tests/e2e   cross-layer UI <-> API <-> DB
tests/bdd   Gherkin feature + step definitions
postman/    Postman collection (run with Newman in Jenkins)
Jenkinsfile CI/CD pipeline        docs/  STLC strategy + defect template
```

## Run locally
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d db                               # PostgreSQL (or use your own, set DATABASE_URL)
python -m shop_app.seed                               # create schema + seed data
python -m shop_app.app &                              # app on http://localhost:5000

pytest -m smoke                 # quick gate
pytest -m regression            # full regression
pytest -m negative              # error handling
pytest -m "api or db"           # no browser needed
pytest -m bdd                   # Gherkin scenarios
HEADLESS=false pytest -m ui     # watch the browser (needs Chrome installed)
pytest -n 2                     # parallel
```
Reports: `reports/report.html`, `reports/junit.xml`, failure screenshots in `reports/screenshots/`.

Postman: import `postman/ecommerce_api.postman_collection.json`, or `npx newman run postman/ecommerce_api.postman_collection.json`.

## Jenkins
Create a Pipeline job from SCM pointing at this repo. Agent needs Python 3, Docker, Node (for Newman) and Chrome.

## Config (env vars)
`BASE_URL`, `DATABASE_URL`, `BROWSER` (chrome|firefox), `HEADLESS`, `TIMEOUT`.

## Pointing it at a different app
Update locators in `pages/`, endpoints in `tests/api/`, and the SQL in `tests/db/`. The structure stays the same.
