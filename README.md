# Crowdfunding Practice Project

A Django-based educational crowdfunding platform built for course practice. Focus is on demonstrating a wide range of typical web app features: custom user model, project publishing, donations, comments, ratings, reports, and basic content aggregation — all backed by a lightweight SQLite database.

## 1. Tech Stack
- Python 3.x
- Django 5.x
- SQLite (default dev DB)
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
- Ratings (1–5) with overwrite capability
- Reporting (project or comment)
- Home page aggregations: highest rated, latest, featured, categories usage
- Admin customization with inlines
- Static & media file handling

## 3. Key Gaps / Improvement Areas
| Area | Gap | Planned Action |
|------|-----|----------------|
| Auth | Email not truly primary, token field reused | Enforce unique email; later transition to email-based auth cleanly |
| Data Integrity | No date constraints, donation uniqueness prevents multiple donations | Add constraints & remove improper unique_together |
| Models | Missing slugs, project updates, reward tiers | Introduce supplemental models |
| Security | Mixed activation/reset token, no rate limiting | Separate flows (later), add simple throttling (optional) |
| UX | No placeholder image, no dashboard, no edit flows | Add fallback image + dashboard + project edit/delete |
| Validation | Raw donation POST, missing form-level checks | Introduce `DonationForm`, model `clean()` methods |
| Performance | Potential N+1 on images/tags | Use `select_related`/`prefetch_related` |
| Testing | No tests at all | Add pytest stack + factories |
| Docs | No README (now), no sample data | Provide README + seed command |
| Maintainability | Monolithic views | Gradually extract service/helpers |

## 4. Planned Data Model Additions
- `Project.slug` (unique, auto from title)
- `ProjectUpdate` (project FK, title, body, created_at)
- `RewardTier` (project FK, title, minimum_amount, description)
- Revise `Donation`: remove `unique_together (project, user)` to allow multiple donations
- Add `CheckConstraint` on `Project` ensuring `end_time > start_time`
- Optional: `Project.is_successful` (set when total donations >= target)
- Validation on `Report` ensuring only one of (project, comment) is set

### Comments Location Decision
Comments (and their replies) remain inside the `projects` app instead of a standalone `comments` app because:
- They are currently only attached to projects (single domain use-case).
- Keeps the codebase smaller for a short 4‑day practice window.
- Avoids added boilerplate (extra app URLs, migrations, generic foreign key or polymorphism) not required by the course rubric.
If later comments are reused across multiple entities (e.g., updates, user profiles, blog posts), a dedicated `comments` app with a more generic relation would then be justified.

## 5. Simplified Task List
Core tasks (course scope):
1. Remove single-donation restriction (drop `unique_together` on `Donation`).
2. Validate project dates (`end_time > start_time`) and block donations to cancelled or expired projects.
3. Introduce `DonationForm` with positive amount validation; refactor donate view.
4. Add placeholder/fallback image logic when a project has no pictures.
5. (Optional) Add `slug` to `Project` and use slug in detail URLs.
6. Implement project edit view (only before any donation exists).
7. Make cancel project action POST-only and enforce <25% funded rule.
8. Add a simple dashboard (lists user’s projects and donations).
9. Enable comment edit & delete (author only) with conditional template buttons.
10. Prevent self-rating (and optionally self-donation if desired).
11. Prefetch related objects in project list/detail (`pictures`, `tags`, `creator`, `category`).
12. Improve progress bar accessibility text and ensure images have alt attributes.
13. Guard templates against missing `project.pictures.first` everywhere.
14. Provide custom 404 and 500 templates.
15. Review admin filters/search; tweak labels if needed.
16. Update README after implementing tasks.
17. Add manual QA checklist section.
18. (Optional) Seed data command or documented manual steps.

Nice-to-have after core:
19. Separate activation vs password reset tokens.
20. Add simple `ProjectUpdate` model for progress notes.
21. Basic homepage caching (short TTL).

Comments stay in the `projects` app for simplicity (see Comments Location Decision above).

## 6. Acceptance Criteria (Condensed)
- Project creation rejects `end_time` earlier than or equal to `start_time`.
- Users can donate multiple times and donation totals/percentages reflect correctly.
- Cancel only works when funding < 25% of target.
- Comment author can edit/delete own comments; others cannot see those controls.
- Creator cannot rate their own project (blocked with message).
- Dashboard page lists only the logged-in user’s projects and donations.
- Placeholder image (or safe rendering) when project has zero images (no template errors).
- (If implemented) Slug-based project URLs load correctly.
## 7. Performance Considerations
- Prefetch project pictures & tags in list/detail views
- Add DB indexes on: `Project(is_cancelled, end_time)`, `Tag.name`, `Category.name`
- Optionally cache homepage aggregated queries (short TTL 60s)

## 8. Security & Safety Notes
- SECRET_KEY currently stored in `settings.py` (acceptable for course, but warn in README)
- Token reuse (activation/reset) flagged for refactor
- Add server-side validation preventing interactions on expired or cancelled projects
- Consider size/type validation for uploaded images (Pillow checks)

## 9. Developer Conventions
- Use snake_case for function names, PascalCase for models
- Keep business logic minimal in views; extract future helpers to `services.py`
- All mutating actions POST-only with CSRF token
- Use Django messages for user feedback; ensure each template renders them

## 10. Quick Start
```bash
# Install deps
pip install -r crowedfunding/requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run dev server
python manage.py runserver
```
Media uploads stored in `media/`. Static assets collected (if needed) into `static/` when running `collectstatic`.

## 11. Future Stretch Ideas
- REST API (Django REST Framework)
- Real-time donation updates (Django Channels)
- Full-text search (PostgreSQL if switching DB)
- Internationalization (translation tags)
- Accessibility improvements (ARIA for progress bars, alt text for images)

## 12. Glossary
- Donation Percentage: `sum(donations) / total_target * 100`
- Featured Project: Flagged manually via admin currently
- Similar Projects: Shared tags excluding current

---

Maintained as an educational codebase—focus on clarity over optimization. Contributions should reference the Sprint task allocation for role alignment (Dev1 / Dev2 / Dev3).
