import { useNavigate } from 'react-router-dom'
import type { Repo } from '../types/api'
import StatusBadge from './StatusBadge'
import { LANG_ICONS } from '../utils/constants'

export default function RepoCard({ repo }: { repo: Repo }) {
  const navigate = useNavigate()
  const isReady  = repo.status === 'READY'
  const isFailed = repo.status === 'FAILED'

  return (
    <div
      onClick={() => navigate(`/repo/${repo.id}`)}
      className="card cursor-pointer hover:border-gray-600 transition-all group"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-white group-hover:text-brand-400 transition-colors truncate">
            {repo.name}
          </h3>
          {repo.url && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{repo.url}</p>
          )}
        </div>
        <StatusBadge status={repo.status} />
      </div>

      {isReady && (
        <div className="flex flex-wrap gap-3 text-xs text-gray-400">
          <span>📄 {repo.file_count} files</span>
          <span>📏 {repo.total_loc?.toLocaleString()} LOC</span>
          {repo.languages && Object.entries(repo.languages).map(([lang, count]) => (
            <span key={lang}>
              {LANG_ICONS[lang] ?? '🔵'} {lang} ({count})
            </span>
          ))}
        </div>
      )}

      {isFailed && repo.error_message && (
        <p className="text-xs text-red-400 mt-2 truncate">{repo.error_message}</p>
      )}

      {isReady && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={e => { e.stopPropagation(); navigate(`/repo/${repo.id}/graph`) }}
            className="text-xs text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-2 py-1 rounded transition-colors"
          >
            🕸 Graph
          </button>
          <button
            onClick={e => { e.stopPropagation(); navigate(`/repo/${repo.id}/ask`) }}
            className="text-xs text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-2 py-1 rounded transition-colors"
          >
            💬 Ask
          </button>
          <button
            onClick={e => { e.stopPropagation(); navigate(`/repo/${repo.id}/dashboard`) }}
            className="text-xs text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-2 py-1 rounded transition-colors"
          >
            📊 Dashboard
          </button>
        </div>
      )}
    </div>
  )
}
