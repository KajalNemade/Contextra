// ── Repo ────────────────────────────────────────────────────────────────────
export interface Repo {
  id: number
  name: string
  status: RepoStatus
  url: string | null
  commit_hash: string | null
  file_count: number
  total_loc: number
  languages: Record<string, number> | null
  error_message: string | null
  created_at?: string
  updated_at?: string
}

export type RepoStatus =
  | 'QUEUED'
  | 'SANITIZING'
  | 'INDEXING'
  | 'PARSING'
  | 'GRAPHING'
  | 'EMBEDDING'
  | 'SUMMARIZING'
  | 'READY'
  | 'FAILED'
  | 'STALE'

// ── Job ─────────────────────────────────────────────────────────────────────
export interface Job {
  id: number
  job_type: string
  status: 'PENDING' | 'RUNNING' | 'DONE' | 'FAILED' | 'CANCELLED'
  stage: string | null
  progress: number
  error_message: string | null
  started_at: string | null
  ended_at: string | null
}

export interface RepoEvent {
  event_type: string
  data: Record<string, any>
  at: string
}

// ── Graph ────────────────────────────────────────────────────────────────────
export interface GraphNode {
  id: string
  type: string
  language?: string
  loc?: number
}

export interface GraphEdge {
  source: string
  target: string
  relation: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphResponse {
  repo_id: number
  graph: GraphData
  layers: Record<string, string[]>
  entry_points: string[]
  circular_dependencies: string[][]
  stats: { total_nodes: number; total_edges: number }
}

// ── Ask / Q&A ────────────────────────────────────────────────────────────────
export interface AskResponse {
  answer: string
  provider: 'ollama' | 'gemini' | 'search_only' | 'none'
  sources: string[]
  confidence: 'high' | 'medium' | 'low'
  chunks_used: number
}

// ── Summary ──────────────────────────────────────────────────────────────────
export interface FileSummary {
  path: string
  summary: string
}

export interface TopFile {
  path: string
  language: string
  loc: number
  is_entry_point: boolean
}

export interface Onboarding {
  summary: string
  steps: string[]
  entry_points: string[]
}

export interface RepoSummary {
  repo_id: number
  name: string
  status: string
  stats: {
    file_count: number
    total_loc: number
    languages: Record<string, number>
  }
  project_summary: string | null
  file_summaries: FileSummary[]
  top_files: TopFile[]
  onboarding: Onboarding
}

// ── Search ───────────────────────────────────────────────────────────────────
export interface SearchResult {
  file_path: string
  function_name: string
  score: number
  body: string
  language?: string
  start_line?: number
  class_name?: string | null
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  search_type: 'semantic' | 'keyword_fallback'
}
