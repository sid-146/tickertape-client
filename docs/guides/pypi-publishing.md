# Publishing to PyPI & TestPyPI

This guide covers how `tickertape-client` is packaged, verified, and published to the [Python Package Index (PyPI)](https://pypi.org).

---

## 1. Automated Publishing via GitHub Actions

The repository includes a production-ready publishing workflow at [`.github/workflows/publish.yml`](https://github.com/sid-146/tickertape-client/blob/main/.github/workflows/publish.yml).

### Method A: PyPI Trusted Publishing (Recommended)

PyPI supports **Trusted Publishing (OIDC)**, which eliminates the need to generate, store, or rotate manual API tokens. GitHub Actions authenticates directly with PyPI using short-lived OpenID Connect tokens.

#### Setting up on PyPI:

1. Log in to [pypi.org](https://pypi.org) (or [test.pypi.org](https://test.pypi.org)).
2. Go to **Account Settings** > **Publishing**.
3. Under **Add a new publisher**, select **GitHub**.
4. Enter the repository details:
    - **Owner:** `sid-146`
    - **Repository name:** `tickertape-client`
    - **Workflow name:** `publish.yml`
    - **Environment name:** `pypi` (or `testpypi` for TestPyPI)
5. Save the configuration.

#### Setting up GitHub Environments:

1. In your GitHub repository, go to **Settings** > **Environments**.
2. Click **New environment** and create:
    - `pypi`
    - `testpypi`
3. (Optional) Set protection rules (e.g. required reviewers) for the `pypi` environment.

---

### Method B: API Token Secret (Alternative Fallback)

If you prefer using traditional API tokens:

1. Generate an API token on [pypi.org](https://pypi.org/manage/account/token/) with upload permissions.
2. In your GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Add the following repository secrets:
    - `PYPI_API_TOKEN`: `pypi-...`
    - `TEST_PYPI_API_TOKEN`: `pypi-...` (if using TestPyPI)

---

## 2. Triggering a Release

### Automated via GitHub Release

1. Update the `version` string in `pyproject.toml` (e.g. `version = "0.1.0"`).
2. Commit and push your changes to `main`.
3. In GitHub, create a new Release with a tag matching your version (e.g. `v0.1.0`).
4. Once you click **Publish release**, GitHub Actions will automatically:
    - Run the test suite (`pytest`)
    - Build source distributions (`.tar.gz`) and wheels (`.whl`)
    - Verify package metadata with `twine check`
    - Securely publish to PyPI

### Manual Trigger via GitHub UI (`workflow_dispatch`)

1. In GitHub, go to the **Actions** tab.
2. Select the **Publish to PyPI** workflow.
3. Click **Run workflow**.
4. Choose whether to target `pypi` (production) or `testpypi` (test).

---

## 3. Manual Publishing via Terminal (`uv` or `twine`)

You can also build and publish locally from your terminal.

### Step 1: Clean and Build Distributions

```bash
uv build --clear
```

This outputs clean artifacts to `dist/`:

- `dist/tickertape_client-<version>-py3-none-any.whl`
- `dist/tickertape_client-<version>.tar.gz`

### Step 2: Validate Metadata

```bash
uvx twine check dist/*
```

Ensure both checks output `PASSED`.

### Step 3: Test Upload to TestPyPI

```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token <TEST_PYPI_TOKEN>
```

Verify your TestPyPI release by installing it into a fresh virtual environment:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tickertape-client
```

### Step 4: Publish to Production PyPI

```bash
uv publish --token <PYPI_TOKEN>
```

Once uploaded, the package will be immediately available at:
`https://pypi.org/project/tickertape-client/`
