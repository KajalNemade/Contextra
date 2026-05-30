import { useState, useEffect, useCallback } from 'react'
import { repoApi, jobsApi } from '../services/api'
import type { Repo, Job } from '../types/api'
import { POLLING_INTERVAL_MS, TERMINAL_STATUSES } from '../utils/constants'

export function useRepo(repoId: number) {
  const [repo, setRepo]       = useState<Repo | null>(null)
  const [jobs, setJobs]       = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [r, j] = await Promise.all([
        repoApi.get(repoId),
        jobsApi.list(repoId),
      ])
      setRepo(r)
      setJobs(j)
      setError(null)
      return r
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Network error')
      return null
    } finally {
      setLoading(false)
    }
  }, [repoId])

  useEffect(() => {
    refresh()
    const interval = setInterval(async () => {
      const r = await refresh()
      if (r && TERMINAL_STATUSES.has(r.status)) clearInterval(interval)
    }, POLLING_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [refresh])

  const currentJob = jobs.find(j => j.status === 'RUNNING') ?? jobs[0] ?? null

  return { repo, jobs, currentJob, loading, error, refresh }
}

export function useRepoList() {
  const [repos, setRepos]     = useState<Repo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await repoApi.list()
      setRepos(data)
      setError(null)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Network error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return { repos, loading, error, refresh }
}
