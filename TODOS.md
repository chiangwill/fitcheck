# Fitcheck — Next Steps

Last updated: 2026-03-25

## High priority (job hunting impact)

- [ ] **Bulk score** — one button scores all visible jobs sequentially with rate limiting (protect ~20 req/day Gemini free-tier quota)
- [ ] **Sort/filter by score** — after scoring, rank highest matches first; add filters for remote_level, salary, japanese_level
- [ ] **Skills gap analysis** — aggregate `missing_skills` across all scored jobs → "Kubernetes missing in 8/12 jobs" to guide what to learn

## Medium priority (quality of life)

- [ ] **Persist scores across refresh** — currently scores disappear on page reload; store in local DB so re-scoring isn't needed
- [ ] **Bookmark / notes** — mark jobs as interested / applied / rejected with a personal note
- [ ] **Auto-score on load** — optionally score all jobs when page loads (rate-limited)

## Integration

- [ ] **Discord notification includes score** — have jp_job_crawler POST to fitcheck score endpoint after scraping so new jobs arrive pre-scored
- [ ] **Export to CSV** — scored jobs with all fields for offline tracking
