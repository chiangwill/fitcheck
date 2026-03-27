const BASE = "http://localhost:8000"

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

// Crawler jobs
export const api = {
  crawlerJobs: {
    list: (allTime = false) =>
      req<import("./types").CrawlerJob[]>(`/crawler-jobs?all_time=${allTime}`),

    batchScores: (ids: string[]) =>
      req<Record<string, import("./types").JobScore>>("/crawler-jobs/scores", {
        method: "POST",
        body: JSON.stringify({ ids }),
      }),

    statuses: (ids: string[]) =>
      req<Record<string, import("./types").JobStatus>>(
        `/crawler-jobs/statuses?ids=${ids.join(",")}`,
      ),

    score: (id: string) =>
      req<import("./types").JobScore>(`/crawler-jobs/${id}/score`, {
        method: "POST",
      }),

    setStatus: (id: string, status: import("./types").JobStatus) =>
      req(`/crawler-jobs/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),

    clearStatus: (id: string) =>
      fetch(`${BASE}/crawler-jobs/${id}/status`, { method: "DELETE" }),
  },

  resume: {
    list: () => req<import("./types").Resume[]>("/resume/versions"),
    setActive: (id: number) =>
      req(`/resume/active/${id}`, { method: "PUT" }),
    delete: (id: number) =>
      req(`/resume/${id}`, { method: "DELETE" }),
  },

  jobs: {
    list: () => req<import("./types").Job[]>("/jobs"),
    get: (id: number) => req<import("./types").Job>(`/jobs/${id}`),
    parse: (url: string) =>
      req<import("./types").Job>("/jobs/parse", {
        method: "POST",
        body: JSON.stringify({ url }),
      }),
  },

  match: {
    list: () => req<import("./types").Match[]>("/match"),
    get: (id: number) => req<import("./types").Match>(`/match/${id}`),
    run: (jobId: number) =>
      req<import("./types").Match>(`/match/${jobId}`, { method: "POST" }),
  },

  generate: {
    coverLetter: (matchId: number, tone: string) =>
      req(`/generate/${matchId}`, {
        method: "POST",
        body: JSON.stringify({ tone }),
      }),
  },

  applications: {
    list: () => req<import("./types").Application[]>("/applications"),
    create: (jobId: number) =>
      req<import("./types").Application>("/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId }),
      }),
    update: (id: number, data: { status?: string; notes?: string }) =>
      req(`/applications/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      req(`/applications/${id}`, { method: "DELETE" }),
  },
}
