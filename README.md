# Swissfy

Django REST backend (`backend/`) and Vue frontend (`frontend/`), set up like
wintersehn. Login goes through [govex](../govex) (authentik, OIDC): swissfy
keeps no passwords, username, email, name, birthdate and avatar come from govex.

## Local development

govex runs as its own stack and has to be up first:

```sh
(cd ../govex && docker compose up -d)
docker compose up --build
```

| Service      | URL                                  |
| ------------ | ------------------------------------ |
| Frontend     | http://localhost:5175                |
| Backend      | http://localhost:8001                |
| Django admin | http://localhost:8001/django-admin/ (admin / admin) |

The ports sit next to wintersehn (5173/8000) and govex (5174), so all three
can run at once.

Backend tests: `docker compose run --rm backend python manage.py test`

## Structure

- `backend/main` – settings, URLs, health check
- `backend/accounts` – govex login (`oidc.py`), profile, legal consent, roles
  (Django groups: Admin, Moderator, Verifiziert, Standard)
- `backend/social` – friend requests, friendships, blocks, nicknames
- `frontend/src` – same layout as wintersehn: `components/{common,layout,legal}`,
  `views`, `router`, `stores`, `lib`, `data` (legal texts in `data/legal`)

## Production

Copy `.env.example` to `.env` and fill it in. The govex client id/secret must
match the `SWISSFY_*` values in govex's `.env`.

- `bin/release` – bumps the version, builds and pushes the images, creates a GitHub release
- `bin/deploy` – pulls the images and swaps the backend without downtime
