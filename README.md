# Amazone

Django storefront. Local development uses PostgreSQL from `.env`. Render uses the `DATABASE_URL` it injects from the linked database.

## Local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Render

`render.yaml` creates a free web service and a free PostgreSQL database.

1. Push this repo to GitHub or GitLab.
2. In Render, choose **New** → **Blueprint** and select the repo.
3. Render generates `SECRET_KEY`, sets `DEBUG=False`, and connects `DATABASE_URL`.
4. After the first deploy, create an admin user with the Render shell:

```bash
python manage.py createsuperuser
```

The build installs dependencies, collects static files, and runs migrations. Gunicorn serves the app. WhiteNoise serves CSS and JavaScript. Do not commit `.env`.
