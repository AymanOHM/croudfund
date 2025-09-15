# Crowdfunding Practice Project

A Django-based educational crowdfunding platform built for course practice. Focus is on demonstrating a wide range of typical web app features: custom user model, project publishing, donations, comments, ratings, reports, and basic content aggregation — all backed by a lightweight SQLite database.

## 1. Tech Stack
- Python 3.x
- Django 5.x
- SQLite (default dev DB) / PostgreSQL (optional via `DATABASE_URL`)
- `django-crispy-forms` + `crispy-bootstrap5`
- Pillow (image handling)
- Bootstrap 5 (UI)

## 2. Current Implemented Features
- User registration with email activation token (console email backend)
- Login / logout / profile view + edit / account deletion
- Password reset (shares activation token field for now)
- Custom user model (`accounts.User`) with profile picture & metadata
- Project creation with multiple images, tags, categories
- Project listing with search (title + tags), category filtering, pagination
- Project detail: donations, progress bar, average rating, recent donations, similar projects, threaded comments, cancel (<25% funded rule)
## Crowdfunding Practice (Concise)

Lightweight Django crowdfunding sandbox: projects with images, tags, donations, ratings, reports, and threaded (1‑level) comment replies. Ships with a seeder for quick realistic data.

### Stack
Python 3 · Django 5 · SQLite (default) or PostgreSQL (`DATABASE_URL`) · crispy-forms (Bootstrap 5) · Pillow.

### Core Features
- Custom user (email + username + mobile) & auth flows
- Project CRUD (edit allowed until first donation), tags, categories, images
- Progress bar, donation percentage, cancellation (<25% funded rule)
- Ratings (1–5, creator excluded) & similar projects by shared tags
- Reports (project/comment) & basic dashboard
- Threaded comments (top-level + replies)
- Seed command for users/projects/donations/ratings/comments

### Quick Start
```bash
pip install -r crowedfunding/requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Sample Data
```bash
python manage.py seed --users 6 --projects 15 --donations 60 --comments 80 --max-replies 2
```
Add `--flush-existing` to wipe projects/categories/tags/donations/comments/ratings (keeps users & superusers).

### Seeder Arguments
`--users` how many regular users to ensure (default 5)
`--projects` number of projects (default 12)
`--donations` donation records (default 40)
`--comments` top-level comments (default 60)
`--max-replies` max replies per top-level comment (default 2)
`--flush-existing` remove prior domain data

### PostgreSQL (optional)
```bash
export DATABASE_URL=postgres://user:pass@localhost:5432/crowdfund_dev
python manage.py migrate
```
Data migration from SQLite:
```bash
python manage.py dumpdata > data.json
export DATABASE_URL=postgres://user:pass@localhost:5432/crowdfund_dev
python manage.py migrate
python manage.py loaddata data.json
```

### Notes
- Slugs auto-generate from titles; `backfill_slugs` command fills blanks.
- Replies limited to one level for simplicity.
- SECRET_KEY hardcoded for local use only.

### Next Ideas
Project updates, reward tiers, API, caching, editing/deleting comments.

---
Short on purpose. See `QA_CHECKLIST.md` for manual test steps.

