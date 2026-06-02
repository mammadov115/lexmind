# LexMind Backend API

A robust FastAPI multi-tenant law firm registration and administration system built using SQLAlchemy 2.0 (with async sqlite/postgresql engines), Pydantic validation, and direct cryptographically secure password hashing using `bcrypt`.

---

## 1. Quick Start

This project uses `uv` for python version management and package dependency locking.

### Prerequisites
Make sure `uv` and `make` are installed on your system.

### Install Dependencies
Run the installation command to initialize the virtual environment and sync packages:
```bash
make install
```

---

## 2. Development Commands (Makefile)

A developer-friendly `Makefile` is configured at the root of the project to manage standard development lifecycle operations:

* **Start the server**: Launches the FastAPI dev server on `http://localhost:8000` with hot-reload enabled.
  ```bash
  make run
  ```
* **Run automated tests**: Executes the async test suite using `pytest` inside an isolated in-memory SQLite database.
  ```bash
  make test
  ```
* **Run Ruff checks (Linting)**: Analyzes code styling, imports, and potential errors.
  ```bash
  make lint
  ```
* **Format code**: Runs Ruff formatting on all python source files.
  ```bash
  make format
  ```
* **Auto-fix lint issues**: Resolves common lint and unused import problems automatically.
  ```bash
  make fix
  ```
* **Run all quality checks**: Runs linter checks, checks formatting, and runs the test suite.
  ```bash
  make check
  ```

---

## 3. Manual API Testing

You can manually test the registration endpoints using the provided shell script:

1. In one terminal, start the FastAPI server:
   ```bash
   make run
   ```
2. In a second terminal, execute the testing script to run scenarios for health check, success registration, duplicate checks, and password strength rejections:
   ```bash
   ./test.sh
   ```
