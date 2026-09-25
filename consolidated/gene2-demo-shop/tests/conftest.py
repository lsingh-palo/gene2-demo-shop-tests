"""Gen-e2 conftest template - mode-aware fixtures.

Vendored into a suite as tests/conftest.py. Works for a standalone run
(config/test_config.json) and for a consolidated suite (config/suite-config.json).

Execution modes (see .github/harness/knowledge/execution-modes.md):
  interactive : headed Chromium, 1 worker, headless guard ACTIVE   (default, Phase 1 parity)
  parallel    : multi-browser + up to 5 workers, headless allowed  (user opted in)
  ci          : headless forced, workers from GENE2_WORKERS         (GENE2_MODE=ci)
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page

try:  # Allure is optional at import time; requirements.txt installs it
    import allure
except ImportError:  # pragma: no cover
    allure = None

WORKER_CAP = 5


# --------------------------------------------------------------------------- config
def _load_config() -> dict:
    here = Path(__file__).parent.parent
    for name in ("config/suite-config.json", "config/test_config.json"):
        p = here / name
        if p.exists():
            data = json.loads(p.read_text())
            data.setdefault("_source", name)
            return data
    return {"_source": "defaults"}


@pytest.fixture(scope="session")
def config() -> dict:
    return _load_config()


@pytest.fixture(scope="session")
def execution_mode(config) -> str:
    if os.environ.get("GENE2_MODE") == "ci":
        return "ci"
    mode = config.get("execution_mode")
    if mode in ("interactive", "parallel", "ci"):
        return mode
    # infer: parallel if a matrix/worker hint exists, else interactive
    if config.get("browsers", ["chromium"]) != ["chromium"] or int(config.get("workers", 1)) > 1:
        return "parallel"
    return "interactive"


@pytest.fixture(scope="session")
def workers(config, execution_mode) -> int:
    raw = os.environ.get("GENE2_WORKERS") or config.get("workers") or (1 if execution_mode == "interactive" else 3)
    n = max(1, int(raw))
    if n > WORKER_CAP:
        print(f"NOTICE: worker count {n} exceeds the cap, running with {WORKER_CAP}")
        n = WORKER_CAP
    return n


@pytest.fixture(scope="session")
def browsers(config) -> list[str]:
    env = os.environ.get("GENE2_BROWSERS")
    if env:
        return env.split()
    return config.get("browsers") or config.get("default_browsers") or ["chromium"]


# --------------------------------------------------------------------------- urls
@pytest.fixture(scope="session")
def app_url(config, pytestconfig):
    """Base URL per app. Precedence: --base-url > GENE2_BASE_URL > config (primary app).

    The override matters: CI points the same suite at staging with --base-url, and the parity
    dual-run (Rule 26) points it at a legacy and a replacement system. Before this, the fixture
    ignored --base-url entirely, so a pipeline's "run against staging" silently ran against
    whatever URL the config held. Non-primary apps take GENE2_APP_URL_<APP> (upper-case name).
    """
    apps = config.get("apps")
    try:
        cli = pytestconfig.getoption("base_url")
    except ValueError:
        cli = None
    override = cli or os.environ.get("GENE2_BASE_URL")

    def _url(app: str | None = None) -> str:
        if apps:
            primary = next((k for k, v in apps.items() if v.get("primary")), next(iter(apps)))
            app = app or primary
            specific = os.environ.get(f"GENE2_APP_URL_{app.upper()}")
            if specific:
                return specific.rstrip("/")
            if app == primary and override:
                return override.rstrip("/")
            return apps[app]["base_url"].rstrip("/")
        if override:
            return override.rstrip("/")
        url = config.get("website_url") or config.get("base_url")
        if not url:
            raise pytest.UsageError("no app URL: set website_url in config/suite-config.json, "
                                    "GENE2_BASE_URL, or --base-url")
        return url.rstrip("/")

    return _url


@pytest.fixture(scope="session")
def base_url(app_url) -> str:
    return app_url()


@pytest.fixture(scope="session")
def credentials(config) -> dict:
    if config.get("credentials_from_env"):
        return {
            "primary": {
                "username": os.environ.get("GENE2_USERNAME", ""),
                "password": os.environ.get("GENE2_PASSWORD", ""),
            }
        }
    creds = config.get("credentials")
    if creds:
        return creds
    # no credentials in the config: the primary login comes from the environment (never from code)
    return {
        "primary": {
            "username": os.environ.get("GENE2_USERNAME", ""),
            "password": os.environ.get("GENE2_PASSWORD", ""),
        }
    }


# --------------------------------------------------------------------- browser args
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, config, execution_mode):
    """Mode-aware. interactive => headed + guard; parallel/ci => allow headless."""
    args = dict(browser_type_launch_args)
    if execution_mode == "interactive":
        # Phase 1 hard guard - headless is blocked in interactive mode
        if config.get("headless"):
            raise RuntimeError(
                "HEADLESS BLOCKED in interactive mode. Use `parallel` or `ci` mode for headless."
            )
        for var in ("HEADLESS", "PLAYWRIGHT_HEADLESS"):
            if os.environ.get(var, "").lower() in ("1", "true", "yes"):
                raise RuntimeError(
                    f"HEADLESS BLOCKED: {var}={os.environ[var]} in interactive mode. "
                    f"Unset it, or run in `parallel`/`ci` mode."
                )
        args["headless"] = False
    elif execution_mode == "ci":
        args["headless"] = True
    else:  # parallel
        args["headless"] = os.environ.get("GENE2_HEADED", "").lower() not in ("1", "true", "yes")
    return args


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, config):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


# --------------------------------------------------------------------------- page
@pytest.fixture
def page(page: Page, config) -> Page:
    page.set_default_timeout(int(config.get("timeout", 30_000)))
    page.set_default_navigation_timeout(60_000)
    page.on("dialog", lambda d: d.dismiss())
    yield page


@pytest.fixture(autouse=True)
def _cleanup(page: Page):
    """Best-effort, idempotent, per-test. Never raises."""
    yield
    try:
        # remove cart-like items if the page has remove buttons
        removers = page.locator("[data-test^='remove-'], button:has-text('Remove')")
        guard = 0
        while removers.count() and guard < 12:
            removers.first.click(timeout=1_500)
            page.wait_for_timeout(200)
            guard += 1
    except Exception:
        pass


# --------------------------------------------------------------------- one set of test ids
_DOC_IDS = {
    "tc_id": re.compile(r"^\s*(TC\w+)"),
    "scenario_key": re.compile(r"\[key:([0-9a-f]+)\]"),
    "plan_step": re.compile(r"\[plan:(P-\d+)\]"),
    "provenance": re.compile(r"provenance:\s*(confirmed against [A-Za-z0-9_:/#.-]+|observed)"),
}


def test_ids(doc: str) -> dict:
    """TC id, scenario key, plan step and provenance from a test's docstring - the same ids the
    manifest and the QMetry sheet use. Missing ones are left out, never invented."""
    out = {}
    for name, pat in _DOC_IDS.items():
        m = pat.search(doc or "")
        if m:
            out[name] = m.group(1).rstrip(".")
    return out


@pytest.fixture(autouse=True)
def _gene2_ids(request, record_property):
    """Put the same ids into JUnit (properties) and Allure (id, labels), so JUnit, Allure, the
    suite manifest and QMetry all name a test the same way."""
    ids = test_ids(request.function.__doc__ or "")
    for name, value in ids.items():
        record_property(name, value)
    if allure is not None:
        module = Path(str(request.fspath)).stem.replace("test_", "", 1)
        allure.dynamic.feature(module)
        if "tc_id" in ids:
            allure.dynamic.id(ids["tc_id"])
            allure.dynamic.label("tc_id", ids["tc_id"])
        if "scenario_key" in ids:
            allure.dynamic.label("scenario_key", ids["scenario_key"])
        if "plan_step" in ids:
            allure.dynamic.story(ids["plan_step"])
        if "provenance" in ids:
            allure.dynamic.tag(ids["provenance"])
            req = re.search(r"confirmed against (\S+)", ids["provenance"])
            if req:
                allure.dynamic.label("requirement", req.group(1))
    yield


@pytest.fixture(autouse=True)
def _trace_on_failure(page: Page, request):
    """A Playwright trace for every failed test (GENE2_TRACE=off to skip), attached to Allure."""
    if os.environ.get("GENE2_TRACE", "on") == "off":
        yield
        return
    started = False
    try:
        page.context.tracing.start(screenshots=True, snapshots=True)
        started = True
    except Exception:
        pass
    yield
    if not started:
        return
    rep = getattr(request.node, "rep_call", None)
    try:
        if rep is not None and rep.failed:
            out = Path("reports/traces")
            out.mkdir(parents=True, exist_ok=True)
            path = out / f"{request.node.name}-{os.environ.get('PYTEST_XDIST_WORKER', 'gw0')}.zip"
            page.context.tracing.stop(path=str(path))
            if allure is not None:
                allure.attach.file(str(path), name="playwright trace", extension="zip")
        else:
            page.context.tracing.stop()
    except Exception:
        pass


# --------------------------------------------------------------------- reporting + heal context
_SELECTOR_IN_MSG = re.compile(r'(?:locator|selector)\(\s*["\']([^"\']+)["\']')
_RESOLVED = re.compile(r"locator resolved to <|unexpected value", re.I)
_NEVER_FOUND = re.compile(r"resolved to 0 elements|waiting for (?:selector|locator)", re.I)
_TIMED_OUT = re.compile(r"timeout|timed out", re.I)


def _looks_like_drift(err: str) -> bool:
    """True only when the element itself could not be found (or matched ambiguously).

    Every Playwright assertion failure's call log contains "waiting for locator(...)", so matching
    on that alone flagged ordinary wrong-value failures as drift (found 2026-09-23: a bug
    reproduction whose locator resolved 9 times, value "2" instead of "1", was sent to the healer).
    If the call log shows the locator RESOLVED, the element exists and the value is wrong - that is
    an assertion failure (a bug or a changed requirement), never something to heal.
    """
    if re.search(r"strict mode violation", err, re.I):
        return True
    if _RESOLVED.search(err):
        return False
    return bool(_NEVER_FOUND.search(err) and _TIMED_OUT.search(err))


def _scenario_title(item) -> str:
    doc = (item.function.__doc__ or "").strip()
    m = re.search(r"\]\s*:?\s*(.+?)(?:\.\s|\.$|$)", doc)
    return (m.group(1) if m else item.name.replace("test_", "").replace("_", " ")).strip()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)  # the trace fixture reads rep_call
    if rep.when != "call" or not rep.failed:
        return
    page = item.funcargs.get("page")
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    if page is not None:
        try:
            out = Path("reports/screenshots/errors")
            out.mkdir(parents=True, exist_ok=True)
            shot = out / f"{item.name}-{worker}.png"
            page.screenshot(path=str(shot))
            if allure is not None:
                allure.attach.file(str(shot), name="screenshot on failure", attachment_type=allure.attachment_type.PNG)
        except Exception:
            pass

    # heal context: when the failure looks like a locator problem, dump what the healer needs
    err = str(getattr(call, "excinfo", "") and call.excinfo.value)
    is_bug_repro = item.get_closest_marker("bug") is not None  # never heal a bug reproduction
    if (page is not None and not is_bug_repro and _looks_like_drift(err)
            and os.environ.get("GENE2_HEAL", "propose") != "off"):
        try:
            sel = _SELECTOR_IN_MSG.search(err)
            hc = {
                "test": item.nodeid,
                "test_name": item.name,
                "scenario_title": _scenario_title(item),
                "intent": _scenario_title(item),
                "url": page.url,
                "broken_selector": sel.group(1) if sel else "",
                "browser": os.environ.get("GENE2_PRIMARY_BROWSER", "chromium"),
                "error_head": err.splitlines()[0][:300],
                "worker": worker,
            }
            d = Path("reports/heal-context")
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{item.name}-{worker}.json").write_text(json.dumps(hc, indent=2))
            try:
                (d / f"{item.name}-{worker}-snapshot.txt").write_text(
                    page.locator("body").inner_text(timeout=2000)[:4000]
                )
            except Exception:
                pass
        except Exception:
            pass


# --------------------------------------------------------------------- known bugs in CI
# A @pytest.mark.bug test reproduces a known product bug: it fails until the bug is fixed. In ci mode
# (GENE2_MODE=ci) or unattended autonomy it is a STRICT expected failure, decided on the exit code so
# every report (JUnit, Allure, QMetry, the PDF) still shows it failed and linked to its Jira bug:
#   - only known bugs failed          -> the run passes (exit 0)
#   - a known-bug test PASSED          -> the run fails: the bug is fixed, flip the test
#   - anything else failed             -> the run fails, as always
# Interactive and parallel runs are unchanged. Jira key: @pytest.mark.bug(jira="KEY-1"), else the
# suite's bug ledger (bugs.json, entry "test" = "<file>::<name>").
_KNOWN = {"failed": [], "fixed": [], "other": []}


def _known_bug_gate() -> bool:
    return os.environ.get("GENE2_MODE") == "ci" or os.environ.get("GENE2_AUTONOMY") == "unattended"


def _bug_ledger() -> dict[str, dict]:
    ledger = Path(__file__).resolve().parents[1] / "bugs.json"
    try:
        bugs = json.loads(ledger.read_text(encoding="utf-8")).get("bugs", [])
    except (OSError, ValueError):
        return {}
    return {b["test"].split("::")[-1]: b for b in bugs if b.get("test") and b.get("status") != "fixed"}


def known_bug_key(item) -> str | None:
    m = item.get_closest_marker("bug")
    if m is None:
        return None
    return m.kwargs.get("jira") or (_bug_ledger().get(item.originalname or item.name) or {}).get("jira")


@pytest.fixture(autouse=True)
def _known_bug_labels(request):
    """Allure: tag each known-bug test and link its Jira issue."""
    if allure is not None and request.node.get_closest_marker("bug") is not None:
        allure.dynamic.tag("known-bug")
        key = known_bug_key(request.node)
        base = os.environ.get("ATLASSIAN_BASE_URL", "").rstrip("/")
        if key:
            allure.dynamic.issue(f"{base}/browse/{key}" if base else key, key)
    yield


def pytest_runtest_logreport(report):
    """Collect outcomes on the controller (works with xdist and reruns: only final reports count)."""
    if report.outcome == "rerun" or not (report.when == "call" or report.failed):
        return
    is_bug = "bug" in report.keywords
    if report.failed:
        _KNOWN["failed" if is_bug and report.when == "call" else "other"].append(report.nodeid)
    elif report.passed and is_bug and report.when == "call":
        _KNOWN["fixed"].append(report.nodeid)


def pytest_sessionfinish(session, exitstatus):
    if not _known_bug_gate():
        return
    if _KNOWN["fixed"]:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    elif exitstatus == pytest.ExitCode.TESTS_FAILED and _KNOWN["failed"] and not _KNOWN["other"]:
        session.exitstatus = pytest.ExitCode.OK


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Point the operator at heal material when there is any; say how known bugs were judged."""
    if _known_bug_gate() and (_KNOWN["failed"] or _KNOWN["fixed"]):
        terminalreporter.write_line(
            f"\n[known bugs] {len(set(_KNOWN['failed']))} failed as expected (strict expected failures)."
            + (" Only known bugs failed: the run passes." if not _KNOWN["other"] and not _KNOWN["fixed"] else ""),
            yellow=True)
        for nodeid in sorted(set(_KNOWN["fixed"])):
            terminalreporter.write_line(
                f"[known bugs] FIXED: {nodeid} passed. Confirm the fix, resolve its Jira bug "
                f"(jira_bug.py --resolve) and flip it into a normal test.", red=True)
    hc = list(Path("reports/heal-context").glob("*.json")) if Path("reports/heal-context").exists() else []
    fb = Path("reports/heal-fallbacks.log")
    if hc:
        terminalreporter.write_line(
            f"\n[heal] {len(hc)} failure(s) look like locator drift - context in reports/heal-context/. "
            f"Run the gene2-self-heal skill (mode: {os.environ.get('GENE2_HEAL', 'propose')}).",
            yellow=True,
        )
    if fb.exists() and fb.stat().st_size:
        terminalreporter.write_line(
            f"[heal] some tests used a fallback locator this run - see reports/heal-fallbacks.log; "
            f"these are repair candidates for the consolidated suite.",
            yellow=True,
        )


def pytest_configure(config):
    # heal material reflects only the current run - clear last run's
    import shutil
    hc = Path("reports/heal-context")
    if hc.exists():
        shutil.rmtree(hc, ignore_errors=True)
    fb = Path("reports/heal-fallbacks.log")
    if fb.exists():
        fb.unlink()
    for marker in (
        "smoke: critical path",
        "functional: standard functional",
        "extended: edge / robustness / security",
        "bug: bug reproduction (fails until fixed)",
        "exploratory: promoted from an exploratory session",
        "flaky: quarantined, excluded from gating with -m 'not flaky'",
        "heal: a test repaired by the self-healing flow (Rule 20)",
    ):
        config.addinivalue_line("markers", marker)
