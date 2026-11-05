# Publishing (maintainers)

Source: https://github.com/jdesaunay/tradingcalendars-python

## One-time setup
1. GitHub: create the **public**, empty repo `jdesaunay/tradingcalendars-python`.
2. PyPI (pypi.org, account with 2FA): Account → Publishing → **Add a new pending publisher**:
   PyPI project `tradingcalendars`, owner `jdesaunay`, repo `tradingcalendars-python`,
   workflow `publish.yml`, environment `pypi`.
3. GitHub repo → Settings → Environments → New environment `pypi`.

## Each release
1. Bump `version` in `pyproject.toml` and `__version__` in `src/tradingcalendars/__init__.py`.
2. GitHub → Releases → Draft a new release, tag `v0.1.0` (matching), Publish.
   The `publish` workflow runs the tests, builds and uploads to PyPI.
