# Contributing Guide

Thank you for your interest in contributing to `tickertape-client`!

---

## Local Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/sid-146/tickertape-client.git
    cd tickertape-client
    ```

2. **Install all dependencies (including dev and docs groups):**
    ```bash
    uv sync --all-groups
    ```

---

## Running Tests

Run the test suite using `pytest`:

```bash
uv run pytest
```

Check coverage:

```bash
uv run pytest --cov=tickertape
```

---

## Documentation Development

Preview the documentation locally with hot-reloading:

```bash
uv run mkdocs serve
```

Open `http://127.0.0.1:8000` in your browser.

Build the static site:

```bash
uv run mkdocs build --strict
```

---

## Pull Request Guidelines

1. Ensure all tests pass.
2. Add unit tests for any new features or bug fixes.
3. Keep code typed and documented with Google-style docstrings.
4. Update `README.md` and `docs/` where appropriate.
