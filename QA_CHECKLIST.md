# QA Checklist

Validated against current implementation status (mid-September 2025). Use this to manually verify core behaviors before delivery.

## 1. Environment & Setup
- [ ] Fresh clone installs dependencies without errors
- [ ] `python manage.py migrate` succeeds
- [ ] Superuser creation works
- [ ] Media directory writeable (`media/` created automatically on first upload)
- [ ] Seed command runs: `python manage.py seed` (no errors)
- [ ] Seed with `--flush-existing` resets domain data (projects/categories/tags/donations/comments/ratings) but keeps users
- [ ] Seed with `--with-images` generates profile & project images
- [ ] Re-run with `--with-images` (no `--force-images`) does not duplicate images
- [ ] Re-run with `--force-images --with-images` regenerates (timestamps or file hashes differ)

## 2. User Accounts
- [ ] Register user -> activation email printed to console -> activation completes
- [ ] Login works with activated user
- [ ] Password reset email printed and allows login with new password
- [ ] Profile edit saves first/last name and profile picture
- [ ] Delete account flow removes user and related owned projects (cascade) (confirm behavior)

## 3. Projects: Creation & Display
- [ ] Create project with valid future start/end -> succeeds
- [ ] Attempt project with end <= start -> validation error shown
- [ ] Multiple images upload -> all appear in carousel
- [ ] Project with zero images -> placeholder displayed (list + detail + home)
- [ ] Project seeded with images has between configured min..max images (default 1..3)
- [ ] Regenerated images (with force) replace previous ones
- [ ] Slug generated and detail accessible at `/projects/<slug>/`
- [ ] Editing allowed before donations, blocked after first donation

## 4. Tags & Categories
- [ ] Enter comma-separated tags -> tags created/associated
- [ ] Duplicate tag names reused rather than duplicated
- [ ] Category filter narrows list correctly
- [ ] Search by tag fragment returns matching projects

## 5. Donations
- [ ] Multiple donations from same user accumulate
- [ ] Donation progress bar updates percentage
- [ ] Donation rejected (message) when project expired
- [ ] Donation rejected (message) when project cancelled
- [ ] Recent donations list shows newest first (limited to 5)
- [ ] Seeded donations visible after seeding

## 6. Cancellation Rules
- [ ] Cancel button visible only to creator and <25% funded
- [ ] POST cancel sets project to cancelled and hides donate UI (after redirect)
- [ ] Repeated cancel attempt gives info message
- [ ] Cancel blocked >=25% funded (error message)

## 7. Ratings
- [ ] User can rate 1–5 and update rating
- [ ] Creator cannot rate own project (message shown)
- [ ] Average rating updates after change

## 8. Comments
- [ ] Root comment posts successfully
- [ ] Reply posts and nests under parent
- [ ] (Future) Edit/delete (NOT IMPLEMENTED YET) – ensure hidden
- [ ] Similar projects exclude current and share at least one tag

## 9. Reports
- [ ] Report project form submits and success message shows
- [ ] Report comment form submits and success message shows
- [ ] Only one of project/comment populated per report record

## 10. Dashboard
- [ ] User projects list only shows current user's projects
- [ ] Donations list only shows current user's donations
- [ ] Links navigate to project detail via slug

## 11. Accessibility & UI
- [ ] All images have meaningful alt text or placeholder alt text
- [ ] Generated avatar images visually show initials (legible size)
- [ ] Project banners have readable overlaid text (sufficient contrast)
- [ ] Progress bars announce percentage via assistive tech (aria-valuenow)
- [ ] Keyboard navigation reaches all interactive controls

## 12. Admin
- [ ] Autocomplete fields load for foreign keys (Project, Donation, etc.)
- [ ] Filters present (category, featured, cancelled, dates)
- [ ] Search by project title and user email works
- [ ] Inline editing shows related objects (pictures, donations, comments, ratings)

## 13. Performance (Spot Checks)
- [ ] Project list view SQL queries (DEBUG toolbar) reasonable (prefetch reduces pictures/tags queries)
- [ ] Detail view avoids N+1 on pictures/comments/tags
- [ ] Indexes exist for `project_cancel_end_idx` and `category.name`
- [ ] Slug lookups use indexed slug field

## 14. Error Handling
- [ ] 404 page renders (set DEBUG=False locally and visit missing URL)
- [ ] 500 page renders (temporary view raising exception with DEBUG=False)

## 15. Security / Integrity
- [ ] Mutating actions (donate, rate, cancel, comment) require login
- [ ] CSRF token present in all forms
- [ ] Non-owner cannot access edit URL (404)
- [ ] Cancel/edit not possible via GET (redirect + message)

## 16. Data Integrity
- [ ] CheckConstraint prevents invalid date save in admin shell
- [ ] Multiple donations sum correctly across different users
- [ ] Tag reuse (no duplicate rows for same name when seeding twice)
- [ ] Image regeneration with `--force-images` does not create orphaned old files (count in media directories stable)

## 17. Logging / Messages
- [ ] Success/error messages appear consistently after actions
- [ ] Seeder outputs counts for Users/Projects/Donations/Ratings/Comments/Replies and Image generation numbers

## 18. Out-of-Scope / Deferred
- [ ] Comment edit/delete (to be implemented)
- [ ] Project updates model
- [ ] Reward tiers
- [ ] Token separation (activation vs reset)
- [ ] Caching layer

---
Add notes below during test execution:

| Area | Observation | Action Needed |
|------|-------------|---------------|
|      |             |               |
