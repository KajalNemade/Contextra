export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const POLLING_INTERVAL_MS = 2500

export const TERMINAL_STATUSES = new Set(['READY', 'FAILED', 'STALE'])

export const STATUS_LABELS: Record<string, string> = {
  QUEUED:      'Queued',
  SANITIZING:  'Scanning for secrets…',
  INDEXING:    'Indexing files…',
  PARSING:     'Parsing code…',
  GRAPHING:    'Building dependency graph…',
  EMBEDDING:   'Generating embeddings…',
  SUMMARIZING: 'Summarizing with AI…',
  READY:       'Ready',
  FAILED:      'Failed',
  STALE:       'Stale — needs reindex',
}

export const LANG_COLORS: Record<string, string> = {
  python:     '#3572A5',
  javascript: '#f1e05a',
  typescript: '#2b7489',
}

export const LANG_ICONS: Record<string, string> = {
  python:     '🐍',
  javascript: '🟨',
  typescript: '🔷',
}

export const MAX_QUESTION_LEN = 500
export const MAX_SEARCH_LEN = 200
