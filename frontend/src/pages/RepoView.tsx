import { useParams, useNavigate } from 'react-router-dom'
import { useRepo } from '../hooks/useRepo'
import StatusBadge from '../components/StatusBadge'
import ProgressBar from '../components/ProgressBar'
import { LANG_ICONS, STATUS_LABELS } from '../utils/constants'

export default function RepoView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const repoId = Number(id)
  const { repo, currentJob, loading, error } = useRepo(repoId)

  if (loading) return (
    <div className="p-8 flex items-center gap-3 text-gray-400">
      <span className="animate-spin text-xl">⟳</span> Loading…
    </div>
  )

  if (error || !repo) return (
    <div className="p-8">
      <div className="card max-w-md text-center py-10">
        <div className="text-3xl mb-3">❌</div>
        <p className="text-red-400">{error ?? 'Repo not found'}</p>
        <button onClick={() => navigate('/')} className="btn-ghost mt-4">← Back</button>
      </div>
    </div>
  )

  const isReady    = repo.status === 'READY'
  const isFailed   = repo.status === 'FAILED'
  const isWorking  = !isReady && !isFailed

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <button onClick={() => navigate('/')} className="text-gray-500 hover:text-white text-xs mb-2 block">
            ← All Repos
          </button>
          <h1 className="text-2xl font-bold text-white">{repo.name}</h1>
          {repo.url && <p className="text-gray-500 text-xs mt-1">{repo.url}</p>}
          {repo.commit_hash && (
            <p className="text-gray-600 text-xs mt-0.5 font-mono">
              {repo.commit_hash.slice(0, 12)}
            </p>
          )}
        </div>
        <StatusBadge status={repo.status} />
      </div>

      {/* Progress (while indexing) */}
      {isWorking && (
        <div className="card mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl animate-spin">⟳</span>
            <div>
              <p className="text-white font-medium">
                {STATUS_LABELS[repo.status] ?? 'Processing…'}
              </p>
              <p className="text-gray-400 text-xs">This page refreshes automatically</p>
            </div>
          </div>
          {currentJob && (
            <ProgressBar progress={currentJob.progress} stage={currentJob.stage} />
          )}

          {/* Pipeline stages visual */}
          <div className="mt-5 flex gap-2 flex-wrap">
            {['INDEXING','PARSING','GRAPHING','EMBEDDING','SUMMARIZING','READY'].map(stage => {
              const stages = ['INDEXING','PARSING','GRAPHING','EMBEDDING','SUMMARIZING','READY']
              const currentIdx = stages.indexOf(repo.status)
              const stageIdx   = stages.indexOf(stage)
              const done    = stageIdx < currentIdx
              const active  = stageIdx === currentIdx
              return (
                <div key={stage} className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border ${
                  done   ? 'border-green-700 bg-green-900/20 text-green-400' :
                  active ? 'border-brand-500 bg-brand-500/10 text-brand-400' :
                           'border-gray-700 text-gray-600'
                }`}>
                  {done ? '✓' : active ? '●' : '○'} {stage}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Error */}
      {isFailed && (
        <div className="card mb-6 border-red-800 bg-red-900/10">
          <h3 className="text-red-400 font-medium mb-2">❌ Indexing Failed</h3>
          <p className="text-red-300 text-sm">{repo.error_message}</p>
        </div>
      )}

      {/* Stats (when ready) */}
      {isReady && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="card text-center">
              <div className="text-3xl font-bold text-white">{repo.file_count}</div>
              <div className="text-gray-400 text-sm mt-1">Files</div>
            </div>
            <div className="card text-center">
              <div className="text-3xl font-bold text-white">
                {repo.total_loc >= 1000
                  ? `${(repo.total_loc / 1000).toFixed(1)}k`
                  : repo.total_loc}
              </div>
              <div className="text-gray-400 text-sm mt-1">Lines of Code</div>
            </div>
            <div className="card text-center">
              <div className="text-3xl font-bold text-white">
                {Object.keys(repo.languages ?? {}).length}
              </div>
              <div className="text-gray-400 text-sm mt-1">Languages</div>
            </div>
          </div>

          {/* Languages breakdown */}
          {repo.languages && Object.keys(repo.languages).length > 0 && (
            <div className="card mb-6">
              <h3 className="text-sm font-medium text-gray-400 mb-3">Languages</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(repo.languages).map(([lang, count]) => (
                  <div key={lang} className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2">
                    <span>{LANG_ICONS[lang] ?? '🔵'}</span>
                    <span className="text-white text-sm capitalize">{lang}</span>
                    <span className="text-gray-500 text-xs">{count} files</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick actions */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: '📊', label: 'Dashboard',       desc: 'File stats & summaries',      path: `/repo/${repoId}/dashboard` },
              { icon: '🕸', label: 'Dependency Graph', desc: 'Visual import relationships', path: `/repo/${repoId}/graph` },
              { icon: '💬', label: 'Ask Questions',   desc: 'AI-powered code Q&A',         path: `/repo/${repoId}/ask` },
            ].map(a => (
              <button
                key={a.label}
                onClick={() => navigate(a.path)}
                className="card text-left hover:border-gray-600 hover:bg-gray-800/50 transition-all group"
              >
                <div className="text-2xl mb-2">{a.icon}</div>
                <div className="font-medium text-white group-hover:text-brand-400 transition-colors text-sm">
                  {a.label}
                </div>
                <div className="text-gray-500 text-xs mt-0.5">{a.desc}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
