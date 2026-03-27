export interface CrawlerJob {
  id: string
  source: string
  title: string | null
  company: string | null
  url: string
  location: string | null
  salary_min: number | null
  salary_max: number | null
  japanese_level: string | null
  remote_level: string | null
  sponsors_visas: boolean
  skills: string[] | null
  published_at: string | null
  first_seen: string
}

export interface JobScore {
  score: number
  missing_skills: string[]
  cached: boolean
}

export type JobStatus = "interested" | "applied" | "rejected"

export interface Resume {
  id: number
  version_name: string
  raw_text: string
  parsed_json: Record<string, unknown> | null
  is_active: boolean
  embedding_id: string | null
  created_at: string
}

export interface Job {
  id: number
  url: string
  title: string | null
  company: string | null
  parsed_json: Record<string, unknown> | null
  created_at: string
}

export interface Match {
  id: number
  resume_id: number
  job_id: number
  score: number
  matched_skills: string[] | null
  missing_skills: string[] | null
  suggestion: string | null
  cover_letter: string | null
  cover_letter_en: string | null
  created_at: string
}

export interface Application {
  id: number
  job_id: number
  status: string
  applied_at: string | null
  notes: string | null
  created_at: string
}
