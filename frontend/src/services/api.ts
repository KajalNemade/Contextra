import axios from 'axios'
import type {
  Repo, Job, RepoEvent, GraphResponse,
  AskResponse, RepoSummary, SearchResponse,
} from '../types/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const api = axios.create({ baseURL: API_URL })

// ── Repos ────────────────────────────────────────────────────────────────────
export const repoApi = {
  list: () => api.get<Repo[]>('/repo').then(r => r.data),
  get:  (id: number) => api.get<Repo>(`/repo/${id}`).then(r => r.data),

  create: (url: string, name?: string) =>
    api.post<Repo>('/repo', { url, name }).then(r => r.data),

  uploadZip: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<Repo>('/repo/upload', form).then(r => r.data)
  },

  delete: (id: number) => api.delete(`/repo/${id}`),
}

// ── Graph ────────────────────────────────────────────────────────────────────
export const graphApi = {
  get: (repoId: number) =>
    api.get<GraphResponse>(`/graph/${repoId}`).then(r => r.data),

  impact: (repoId: number, filePath: string) =>
    api.get(`/graph/${repoId}/impact/${filePath}`).then(r => r.data),
}

// ── Ask / Q&A ────────────────────────────────────────────────────────────────
export const askApi = {
  ask: (repoId: number, question: string, topK = 5) =>
    api.post<AskResponse>('/ask', {
      repo_id: repoId,
      question,
      top_k: topK,
    }).then(r => r.data),
}

// ── Summary ──────────────────────────────────────────────────────────────────
export const summaryApi = {
  get: (repoId: number) =>
    api.get<RepoSummary>(`/summary/${repoId}`).then(r => r.data),
}

// ── Search ───────────────────────────────────────────────────────────────────
export const searchApi = {
  search: (repoId: number, q: string, topK = 10) =>
    api.get<SearchResponse>(
      `/search/${repoId}?q=${encodeURIComponent(q)}&top_k=${topK}`
    ).then(r => r.data),
}

// ── Jobs ─────────────────────────────────────────────────────────────────────
export const jobsApi = {
  list:   (repoId: number) => api.get<Job[]>(`/jobs/${repoId}`).then(r => r.data),
  events: (repoId: number) => api.get<RepoEvent[]>(`/jobs/${repoId}/events`).then(r => r.data),
}

export default api
