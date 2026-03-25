# Fitcheck — Next Steps

Last updated: 2026-03-25

## In progress (current sprint)

- [x] **Persist scores + preload** — `POST /crawler-jobs/scores` + `GET /crawler-jobs/statuses` batch endpoints; UI loads cached scores + statuses in parallel on page open (scores already in Match table, just not displayed on load)
- [x] **Sort by score** — toggle "依日期" ↔ "依評分"; secondary sort by `first_seen` desc for ties
- [x] **Bulk score** — "一鍵評分全部" button; quota warning shown (⚠️ 批量評分將消耗約 15 次 Gemini 每日配額); calls POST sequentially with `await asyncio.sleep(4)` between calls; progress "Scoring 3/15…"; snackbar "12/15 成功，3 失敗"
- [x] **Skills gap summary** — banner: "Kubernetes missing in 8/12 jobs · AWS missing in 6/12 jobs" using top 5 missing skills by frequency; hide until ≥1 job scored
- [x] **Quick status chips** — 感興趣 / 已投履 / 不適合 per job card; new `CrawlerJobStatus` model + PATCH endpoint; upsert on repeat; DELETE endpoint for toggle-off

## Medium priority (quality of life)

- [ ] **Filter panel** — filter chips above job list for `remote_level`, `japanese_level`, salary range; fields already in every Supabase job row; ~50 LOC UI only
- [ ] **Auto-score on load** — optionally score all jobs when page loads; build only after bulk score is stable (quota risk if misconfigured)
- [ ] **Bookmark / notes** — full notes field per job (the quick status chips in the current sprint cover the core need; this adds a text note)
- [ ] **Bulk score resume state** — if user navigates away during batch, progress indicator is lost (but scores ARE saved and preloaded correctly on return); show "N jobs scored since last visit" banner instead of silent partial state; depends on bulk score shipping first

## Integration

- [ ] **Discord notification includes score** — have jp_job_crawler POST to fitcheck `POST /crawler-jobs/{id}/score` endpoint after scraping so new jobs arrive pre-scored; endpoint is already idempotent/cached
- [ ] **Export to CSV** — scored jobs with all fields for offline tracking
