workflow badge: [![QA Automation](https://github.com/benbug17/e-com_qa/actions/workflows/tests.yml/badge.svg)](https://github.com/benbug17/e-com_qa/actions/workflows/tests.yml)

# E-Commerce Quality Automation Framework

UI, API, database and cross-layer test automation for a demo e-commerce shop.

**Stack:** Python 3.12 · Selenium · Pytest · Page Object Model · Requests · Postman/Newman · PostgreSQL · pytest-bdd · Docker · Jenkins · GitHub Actions

The repo includes a small Flask + PostgreSQL shop (`shop_app/`) as the system under test, so every layer has something real to test.

---

**Markers:** `smoke` (10 tests) · `regression` · `negative` · `api` · `db` · `ui` · `e2e` · `bdd`

---

## 1. Prerequisites

- Python 3.12, Git, Google Chrome (for local browser runs)
- Docker Desktop, **running** before any `docker` command (wait for "Engine running")
- Windows PowerShell notes: `&` cannot background a process (use two terminals), and environment variables are set with `$env:NAME="value"`

---

## 2. Setup and run commands

### 2.1 Local (app on your machine, PostgreSQL in Docker)

powershell:
```
pip install -r requirements.txt
docker compose up -d db                  # PostgreSQL on 127.0.0.1:5432
python -m shop_app.seed                  # create schema + seed data
```

Terminal 1 (leave running):
powershell:
```
python -m shop_app.app                   # http://127.0.0.1:5000
```

Terminal 2:
powershell:
```
pytest -m smoke                          # 10 critical-path tests
pytest -m "api or db"                    # no browser needed
pytest -m regression
pytest -m negative
pytest -m bdd
pytest                                   # everything (59 tests)
pytest -n 2                              # parallel (see issue 7)
$env:HEADLESS="false"; pytest -m smoke   # watch the browser
1..25 | ForEach-Object { pytest tests/e2e -k add_to_cart -q }   # repeat a test to hunt flakes
```

Outputs: `reports/report.html`, `reports/junit.xml`, `reports/screenshots/`.
Environment variables: `BASE_URL`, `DATABASE_URL`, `BROWSER` (chrome|firefox), `HEADLESS`, `TIMEOUT`. Defaults use `127.0.0.1`, not `localhost` (see issue 2).

### 2.2 Docker (same stack CI uses)

powershell:
```
docker compose -f docker-compose.ci.yml -p qa-ci build                                # first build: 5-25 min
docker compose -f docker-compose.ci.yml -p qa-ci run --rm tests                       # smoke suite
docker compose -f docker-compose.ci.yml -p qa-ci run --rm tests pytest -m regression
docker compose -f docker-compose.ci.yml -p qa-ci run --rm newman                      # Postman collection
```

### 2.3 Jenkins (in Docker)

powershell:
```
docker compose -f docker-compose.jenkins.yml up -d --build
docker compose -f docker-compose.jenkins.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Then in the browser:
1. Open `http://localhost:8080`, paste the password, install suggested plugins, create the admin user.
2. **New Item** → `ecommerce-qa` → **Pipeline** → Definition **Pipeline script from SCM** → SCM **Git**.
3. Repository URL: your repo. Branch: `*/main` (check with `git branch`). Script Path: `Jenkinsfile`. Save.
4. **Build Now** (first run), then **Build with Parameters** (`SUITE`: smoke / regression / negative / all; `PARALLEL`).
5. Report: build → **Artifacts** → click the `report.html` filename to download it (the *view* link renders blank, see section 6).

Private repos need a GitHub personal access token added as Jenkins credentials.

### 2.4 GitHub Actions

Workflow file: `.github/workflows/tests.yml`. It runs the smoke suite on every push. To run more: **Actions → QA Automation → Run workflow** and choose the suite. Download the `reports` artifact from the run page.

---

## 3. Shutdown commands

### Local
powershell:
```
# Terminal 1: press Ctrl+C to stop the app
Remove-Item Env:HEADLESS                 # only if you set it for a headed run
docker compose stop db                   # stop PostgreSQL, keep the container
docker compose down                      # or: stop and remove it (seed.py re-creates the data)
```

### Docker CI stack
powershell:
```
docker compose -f docker-compose.ci.yml -p qa-ci down -v
```

### Jenkins
powershell:
```
docker compose -f docker-compose.jenkins.yml stop       # pause; jobs and users are kept
docker compose -f docker-compose.jenkins.yml down       # remove the container; jenkins_home volume is kept
docker compose -f docker-compose.jenkins.yml down -v    # DESTRUCTIVE: also deletes jobs, users and settings
```
To start it again later: `docker compose -f docker-compose.jenkins.yml start` (after `stop`) or `up -d` (after `down`).

### Check for leftovers
powershell:
```
docker ps
docker ps -a --filter "name=qa-ci"
docker compose -p qa-ci-1 down -v        # remove a leftover pipeline stack (replace 1 with the build number)
```

### Reclaim disk space
powershell:
```
docker system prune -a                   # removes unused images and cache; the next build is slow again
```

---

## 4. Error log: what failed, why, and how it was fixed

Each entry lists what we saw, the root cause, where the fix lives, and how confident we are that it is resolved. Where a cause was inferred rather than proven, it says so.

### Issue 1: BDD checkout times out in headless mode (login race)

- **Symptom:** `TimeoutException` waiting for the checkout button; headed runs passed.
- **Root cause:** the login step clicked Login and the next step immediately loaded `/cart`, before the response had set the session cookie. The app redirected back to the login page, so no checkout button existed. Slower headed runs hid the race.
- **Where:** `tests/bdd/test_checkout_bdd.py` (login step), `logged_in` fixture in `tests/conftest.py`.
- **Fix:** after login, wait for the products page title before doing anything else.
- **Status:** the first fix did not fully remove the failure (see issue 4). Resolved after both fixes; later runs passed.

### Issue 2: API/DB tests very slow (148 s for 38 tests)

- **Symptom:** simple HTTP and SQL tests took minutes.
- **Root cause (likely):** on Windows, `localhost` can resolve to IPv6 first and wait for a timeout before falling back to IPv4.
- **Where:** `config/settings.py`.
- **Fix:** default `BASE_URL` and `DATABASE_URL` use `127.0.0.1`.
- **Status:** run time dropped to about 54 s, which is consistent with the explanation, but the cause was not isolated further. The remaining time is mostly the per-test database rebuild.

### Issue 3: `StaleElementReferenceException` after add-to-cart

- **Symptom:** clicking the cart link right after adding a product failed with "stale element reference".
- **Root cause:** add-to-cart submits a form and the page reloads. The cart link was located on the old page, and the reload invalidated it before the click.
- **Where:** `pages/base_page.py`, `pages/products_page.py` (`add_to_cart`).
- **Fix:** retry on stale elements inside waits; `add_to_cart` waits until the cart badge count increases before returning.
- **Status:** resolved for the tests that failed.

### Issue 4: BDD checkout fails again after the login fix (navigation by URL)

- **Symptom:** `TimeoutException` on the checkout button even after issue 1's fix; screenshots were missing because the step ran during fixture setup.
- **Root cause (inferred):** the step reached the cart by typing the `/cart` URL, while the passing UI tests clicked the cart link; the session was not reliably in place on a direct load. It was not reproduced on the build machine (no browser there).
- **Where:** the `I checkout` step in `tests/bdd/test_checkout_bdd.py`; the failure hook in `tests/conftest.py`.
- **Fix:** navigate by clicking the cart link like the other tests; failure screenshots and the current URL are now captured for **setup** failures too.
- **Status:** resolved; the BDD scenarios passed in all later runs.

### Issue 5: Intermittent failure in `test_ui_add_to_cart_persists_in_db`

- **Symptoms:** (a) `assert 1 == 2`, the DB showed quantity 1 after two adds; (b) in a 10-run loop, 1 failure with `Node with given id does not belong to the document`.
- **Root cause:** (b) is another page-reload timing error. Selenium reports it as a generic `WebDriverException`, so the earlier stale-element retry missed it. The cause of (a) was never conclusively explained; the same reload timing is the most plausible reading, but a lost second click was not ruled out.
- **Where:** `pages/base_page.py`, `pages/products_page.py`, `tests/e2e/test_cross_layer.py`.
- **Fix:** `BasePage` now polls through a helper that retries only on transient reload errors (stale element, no such element, "does not belong to the document") and re-raises everything else; `click` finds and clicks in one attempt; `text` reads inside the retry; the test asserts the UI badge shows 2 before checking the DB, so a future failure shows which layer is wrong.
- **Status:** fix provided; confirm with the 25-run loop in section 3.1. If the badge shows 2 but the DB shows 1, treat it as a real application defect and log it with `docs/defect_report_template.md`.

### Issue 6: `test_remove_item_from_cart` fails (assertion has no wait)

- **Symptom:** `assert cart.is_empty()` was False even though the item had been removed.
- **Root cause:** remove submits a form and reloads the page. `is_empty()` checked for the "empty cart" text once, instantly, so it sometimes still saw the old page. `test_logout_returns_to_login` has the same pattern.
- **Where:** `is_present` in `pages/base_page.py`.
- **Fix:** `is_present` waits up to 3 seconds for the element before returning False.
- **Status:** fix provided; repeat `pytest tests/ui -k "remove or logout"` in a loop to confirm. Rule going forward: anything asserted right after a click or form submit must wait for the new page.

### Issue 7: `pytest -n 2` produces random failures (shared database)

- **Symptoms:** four unrelated tests failed only in parallel: order lookup returned 404, the cart showed 1 row instead of 2, the cart badge read 4 instead of 2, a stock check timed out.
- **Root cause:** every test resets the database, and both workers shared one database and one app. One worker's reset wiped the other's data mid-test, and both shared the same user's cart.
- **Where:** `tests/conftest.py` (new `isolated_environment` fixture), `utils/api_client.py`.
- **Fix:** under pytest-xdist each worker gets its own database (`shop_gw0`, `shop_gw1`) and its own app server (ports 5100+). `ApiClient` reads `BASE_URL` at call time instead of import time. Serial runs are unchanged. The database user needs permission to create databases (the Docker setup's `qa` user has it).
- **Status:** verified with the API, DB and non-browser cross-layer tests (40 of 40 with `-n 2`, 38 of 38 serial, no leftover worker databases). Parallel **browser** runs were not verified on the build machine; run `pytest -n 2` and report anything that fails.

### Issue 8: Tests fail inside Docker with `FileNotFoundError: /app/features/checkout.feature`

- **Symptom:** BDD test collection crashed; only 56 of 59 tests were collected; the traceback showed a `C:\Users\...` path inside a Linux container.
- **Root cause:** `.dockerignore` only excluded a top-level `__pycache__`. Python bytecode compiled on Windows (containing Windows file paths) was copied into the image, and pytest-bdd resolved the feature file relative to the stale path.
- **Where:** `.dockerignore`.
- **Fix:** exclude caches in every folder: `**/__pycache__` and `**/*.pyc`.
- **Status:** resolved; 59 tests collected and the smoke suite passed in the container.

### Issue 9: Every browser test fails in Docker with `net::ERR_SSL_PROTOCOL_ERROR`

- **Symptom:** API and DB tests passed in the container, but all browser tests failed; the failure URL read `https://app:5000/` although the config said `http://`.
- **Root cause (inferred from the URL change):** the Docker service was named `app`, and `.app` is a real top-level domain that Chrome automatically upgrades to HTTPS. The demo server only speaks HTTP. Python's `requests` does not apply this rule, which is why non-browser tests passed.
- **Where:** `docker-compose.ci.yml`.
- **Fix:** rename the service to `shopapp` and update `BASE_URL` and the Newman `baseUrl` to `http://shopapp:5000`. Avoid hostnames ending in `.app`, `.dev` or other HTTPS-only TLDs.
- **Status:** resolved; the smoke suite passed in the container after the rename.

### Issue 10: First Jenkins build fails: `pytest: error: argument -m: expected one argument`

- **Symptom:** the Newman stage passed, the pytest stage exited with code 4; the log showed `ARGS=-m ` with nothing after it.
- **Root cause:** a parameterized pipeline's first run happens before Jenkins has registered the parameters, so `SUITE` was empty.
- **Where:** `Jenkinsfile` (Pytest stage).
- **Fix:** default the values in the script: `SUITE="${SUITE:-smoke}"` and `PARALLEL="${PARALLEL:-false}"`.
- **Status:** resolved; the next build (via Build with Parameters) passed.

---

## 6. Pitfalls and behaviours to know about (not failures, but they cost time)

- **Pytest HTML report looks blank in Jenkins:** Jenkins' content security policy blocks the report's scripts. Download `report.html` from Artifacts and open it locally.
- **First Docker build is very slow** (the Jenkins build took about 27 minutes): Chromium and its dependencies are around 750 MB. The log can sit quiet at "unpacking" for several minutes. Later builds use the cache.
- **Newman can hide failures:** the GitHub Actions workflow originally had `continue-on-error: true` on the Newman step, so the run could be green while Postman failed. Remove that line once Newman has passed (it has).
- **GitHub Actions notices:** a Node.js 20 deprecation warning for some actions, and a notice that `ubuntu-latest` moves to Ubuntu 26 on October 19, 2026. Pin the runner (`runs-on: ubuntu-24.04`) and bump action versions to keep runs stable.
- **Jenkins runs as root with the Docker socket mounted.** That is acceptable for a local learning setup, not for a shared server.
- **Port clashes:** the local `docker-compose.yml` publishes 5432; the CI stack publishes nothing, so both can run side by side.

---

## 8. Defect and test process

STLC mapping and the defect workflow live in `docs/test_strategy_stlc.md` and `docs/defect_report_template.md`. A defect report should include the linked test ID, steps, expected vs actual result, environment, and evidence (screenshot from `reports/screenshots/`, API response or SQL output).
