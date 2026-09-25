#!/usr/bin/env bash
# Run this suite with one command. The suite does not need the harness: copy this folder anywhere.
#
#   ./run.sh                          local: headed, 1 worker, the level in pytest.ini
#   ./run.sh --ci                     pipeline: headless, parallel, JUnit + HTML + Allure; known-bug
#                                     tests (@pytest.mark.bug) are strict expected failures
#   ./run.sh -m smoke -k checkout     anything else goes to pytest as is
#
# Settings (environment, all optional):
#   GENE2_BASE_URL     the app under test (else config/suite-config.json)
#   GENE2_APP_START    a command that starts the app under test, when it is not already reachable
#                      (for example a local server in a pipeline); it is stopped when the run ends
#   GENE2_BROWSERS     "chromium firefox webkit" (--ci; default chromium)
#   GENE2_WORKERS      1-5 (--ci; default 3)
#   GENE2_NO_VENV=1    use the current Python instead of .venv (default in CI, where CI=true)
#   PYTHON             the Python to use (default python3)
# Reports: <suite>/reports/ (paths you pass to pytest are relative to the suite folder).
# Exit code: pytest's (0 = all passed).
set -euo pipefail

SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
CI_MODE=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --ci) CI_MODE=1 ;;
    -h|--help) sed -n '2,19p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) ARGS+=("$a") ;;
  esac
done

# 1. Python environment: a .venv next to the suite, reinstalled only when requirements.txt changes
if [ "${GENE2_NO_VENV:-}" != "1" ] && [ "${CI:-}" != "true" ]; then
  [ -d "$SUITE/.venv" ] || "$PY" -m venv "$SUITE/.venv"
  PY="$SUITE/.venv/bin/python"
fi
BROWSERS="${GENE2_BROWSERS:-chromium}"
STAMP="$("$PY" -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()+' '+sys.argv[2])" "$SUITE/requirements.txt" "$BROWSERS")"
MARK="$SUITE/.venv/.gene2-installed"
[ -d "$SUITE/.venv" ] || MARK="$SUITE/.gene2-installed"
if [ ! -f "$MARK" ] || [ "$(cat "$MARK")" != "$STAMP" ]; then
  echo "run.sh: installing requirements and browsers ($BROWSERS)"
  "$PY" -m pip install -q -r "$SUITE/requirements.txt"
  "$PY" -m playwright install $BROWSERS
  echo "$STAMP" > "$MARK"
fi

# 2. The app under test, only when asked to start it
APP_PID=""
cleanup() { [ -n "$APP_PID" ] && kill "$APP_PID" 2>/dev/null || true; }
trap cleanup EXIT
if [ -n "${GENE2_APP_START:-}" ]; then
  echo "run.sh: starting the app under test: $GENE2_APP_START"
  bash -c "$GENE2_APP_START" > "$SUITE/app-under-test.log" 2>&1 &
  APP_PID=$!
  URL="${GENE2_BASE_URL:-$("$PY" -c "import json,sys;c=json.load(open(sys.argv[1]));print(c.get('website_url') or c.get('base_url') or '')" "$SUITE/config/suite-config.json")}"
  "$PY" - "$URL" <<'EOF'
import sys, time, urllib.request
url, deadline = sys.argv[1], time.time() + 60
while time.time() < deadline:
    try:
        urllib.request.urlopen(url, timeout=2); sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(f"run.sh: the app did not answer at {url} within 60 s (see app-under-test.log)")
EOF
fi

# 3. The run
OPTS=()
[ -n "${GENE2_BASE_URL:-}" ] && OPTS+=(--base-url "$GENE2_BASE_URL")
if [ "$CI_MODE" = "1" ]; then
  export GENE2_MODE=ci
  for b in $BROWSERS; do OPTS+=(--browser "$b"); done
  OPTS+=(-n "${GENE2_WORKERS:-3}" --dist loadgroup --junitxml=reports/junit.xml)
fi
cd "$SUITE"   # pytest.ini, config/ and reports/ are relative to the suite folder
set +e
"$PY" -m pytest ${OPTS[@]+"${OPTS[@]}"} ${ARGS[@]+"${ARGS[@]}"}
RC=$?
set -e
echo "run.sh: reports in $SUITE/reports/ (HTML, Allure results$( [ "$CI_MODE" = 1 ] && echo ', JUnit' )). Re-run: $0 $*"
exit $RC
