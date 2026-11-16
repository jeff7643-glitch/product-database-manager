# Product database manager

A small Flask application for managing a PostgreSQL product catalog. It supports administrator login, validated product creation and editing, deletion, CSV imports, and searchable/filterable product listings.

## Requirements

- Python 3.10+
- PostgreSQL 12+

## Setup

1. Create a PostgreSQL database (for example, `product_catalog`) and configure `DATABASE_URL` for an application user with permission to create tables and manage products.
2. Create and activate a virtual environment, then install dependencies:

   ```sh
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. Generate the secret and password hash with:

   ```sh
   python -c "import secrets; print(secrets.token_hex(32))"
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('choose-a-strong-password'))"
   ```

   Set `SECRET_KEY` to the generated secret, `ADMIN_PASSWORD_HASH` to the generated hash, and configure `DATABASE_URL` and `ADMIN_USERNAME`. The password hash contains `$` characters, so wrap its value in single quotes in `.env` (for example, `ADMIN_PASSWORD_HASH='scrypt:...$...'`) before exporting the settings with `set -a && . ./.env && set +a` in a POSIX shell. Flask does not load `.env` automatically. Keep real credentials out of source control. Set `SESSION_COOKIE_SECURE=1` when serving the app over HTTPS.

4. Initialize the table and start the development server:

   ```sh
   flask --app app init-db
   flask --app app run
   ```

   Open `http://127.0.0.1:5000` and log in with the configured administrator credentials. For production, use a WSGI server behind HTTPS rather than Flask's development server.

## CSV format

The first row must include `sku`, `name`, and `price`. The optional columns are `quantity`, `category`, and `description`. Imports are validated before writing and run in a single transaction; duplicate SKUs (including existing products) reject the complete import. Files may contain up to 5,000 data rows and must be UTF-8 encoded.

Example:

```csv
sku,name,price,quantity,category,description
MUG-001,Ceramic mug,12.50,30,Kitchen,Blue glazed ceramic mug
```
