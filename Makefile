PY := .venv/bin/python

.PHONY: demo install test eval e2e serve

demo: install test eval
	@echo "Demo complete — see the newest report in eval/reports/"

install:
	test -d .venv || python3.12 -m venv .venv
	.venv/bin/pip install -q -r requirements.txt

test:
	$(PY) -m pytest -q

eval:
	$(PY) -m eval.regression_runner

e2e:
	cd tests/e2e && npm install --no-fund --no-audit && npx playwright install chromium && npx playwright test

serve:
	$(PY) -m uvicorn app.server:app --port 8000
