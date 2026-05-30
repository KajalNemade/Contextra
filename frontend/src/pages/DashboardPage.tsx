import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { summaryApi } from '../services/api'
import type { RepoSummary } from '../types/api'
import { LANG_ICONS } from '../utils/constants'

function SectionHeader({ title }: { title: string }) {
  return (
    <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{title}</h2>
  )
}

export default function DashboardPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [summary, setSummary]  = useState<RepoSummary | null>(null)
  const [loading, setLoading]  = useState(true)
  const [error, setError]      = useState('')

  useEffect(() => {
    summaryApi.get(Number(id))
      .then(setSummary)
      .catch(e => setError(e?.response?.data?.detail ?? 'Failed to load'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="p-8 text-gray-400 flex items-center gap-2">
      <span className="animate-spin">⟳</span> Loading dashboard…
    </div>
  )

  if (error) return (
    <div className="p-8">
      <div className="card border-red-800 text-red-400">{error}</div>
    </div>
  )

  if (!summary) return null

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Back */}
      <button onClick={() => navigate(`/repo/${id}`)} className="text-gray-500 hover:text-white text-xs mb-6 block">
        ← Overview
      </button>

      <h1 className="text-2xl font-bold text-white mb-6">{summary.name} — Dashboard</h1>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-3 mb-8">
        {[
          { label: 'Files',    value: summary.stats.file_count },
          { label: 'LOC',      value: summary.stats.total_loc >= 1000
                                       ? `${(summary.stats.total_loc/1000).toFixed(1)}k`
                                       : summary.stats.total_loc },
          { label: 'Languages', value: Object.keys(summary.stats.languages).length },
          { label: 'Status',   value: summary.status },
        ].map(s => (
          <div key={s.label} className="card text-center">
            <div className="text-2xl font-bold text-white">{s.value}</div>
            <div className="text-gray-400 text-xs mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left col */}
        <div className="col-span-2 space-y-6">
          {/* Project summary */}
          {summary.project_summary && (
            <div>
              <SectionHeader title="AI Project Summary" />
              <div className="card">
                <p className="text-gray-300 text-sm leading-relaxed">{summary.project_summary}</p>
              </div>
            </div>
          )}

          {/* Top files */}
          <div>
            <SectionHeader title="Largest Files" />
            <div className="card p-0 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left text-xs text-gray-500 px-4 py-2.5 font-medium">File</th>
                    <th className="text-right text-xs text-gray-500 px-4 py-2.5 font-medium">LOC</th>
                    <th className="text-right text-xs text-gray-500 px-4 py-2.5 font-medium">Lang</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.top_files.map((f, i) => (
                    <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/40 transition-colors">
                      <td className="px-4 py-2.5 text-gray-300 font-mono text-xs truncate max-w-[280px]">
                        {f.is_entry_point && <span className="mr-1.5 text-yellow-400" title="Entry point">★</span>}
                        {f.path}
                      </td>
                      <td className="px-4 py-2.5 text-right text-gray-400 text-xs">{f.loc.toLocaleString()}</td>
                      <td className="px-4 py-2.5 text-right text-xs">
                        <span className="text-gray-500">{LANG_ICONS[f.language] ?? '🔵'} {f.language}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* File summaries */}
          {summary.file_summaries.length > 0 && (
            <div>
              <SectionHeader title="File Summaries (AI)" />
              <div className="space-y-2">
                {summary.file_summaries.slice(0, 8).map((fs, i) => (
                  <div key={i} className="card">
                    <div className="text-xs text-brand-400 font-mono mb-1">{fs.path}</div>
                    <div className="text-gray-300 text-sm">{fs.summary}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right col — onboarding */}
        <div className="space-y-4">
          <div>
            <SectionHeader title="Onboarding Guide" />
            <div className="card">
              <p className="text-gray-300 text-sm leading-relaxed mb-4">
                {summary.onboarding.summary}
              </p>
              <div className="space-y-2">
                {summary.onboarding.steps.map((step, i) => (
                  <div key={i} className="flex gap-2 text-xs text-gray-400">
                    <span className="text-brand-400 font-bold flex-shrink-0">{i + 1}.</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>

              {summary.onboarding.entry_points.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-800">
                  <div className="text-xs text-gray-500 mb-2">Entry Points</div>
                  {summary.onboarding.entry_points.map((ep, i) => (
                    <div key={i} className="text-xs text-yellow-400 font-mono mb-1">★ {ep}</div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Languages */}
          <div>
            <SectionHeader title="Languages" />
            <div className="card space-y-2">
              {Object.entries(summary.stats.languages).map(([lang, count]) => (
                <div key={lang} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">
                    {LANG_ICONS[lang] ?? '🔵'} {lang}
                  </span>
                  <span className="text-xs text-gray-500">{count} files</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick nav */}
          <div className="card space-y-2">
            <button
              onClick={() => navigate(`/repo/${id}/graph`)}
              className="w-full text-left text-sm text-gray-300 hover:text-white flex items-center gap-2 py-1 transition-colors"
            >
              🕸 View Dependency Graph
            </button>
            <button
              onClick={() => navigate(`/repo/${id}/ask`)}
              className="w-full text-left text-sm text-gray-300 hover:text-white flex items-center gap-2 py-1 transition-colors"
            >
              💬 Ask Questions
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}