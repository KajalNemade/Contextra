import { useNavigate } from 'react-router-dom'
import { useRepoList } from '../hooks/useRepo'
import RepoCard from '../components/RepoCard'

export default function HomePage() {
  const { repos, loading } = useRepoList()
  const navigate = useNavigate()

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Repositories</h1>
          <p className="text-gray-400 text-sm">
            {repos.length} repo{repos.length !== 1 ? 's' : ''} indexed
          </p>
        </div>
        <button onClick={() => navigate('/upload')} className="btn-primary">
          ➕ Add Repository
        </button>
      </div>

      {loading ? (
        <div className="grid gap-3">
          {[1,2,3].map(i => (
            <div key={i} className="card animate-pulse h-24 bg-gray-800" />
          ))}
        </div>
      ) : repos.length === 0 ? (
        <div className="card text-center py-16">
          <div className="text-5xl mb-4">📂</div>
          <h2 className="text-lg font-semibold text-white mb-2">No repositories yet</h2>
          <p className="text-gray-400 text-sm mb-6">
            Add a GitHub URL or upload a ZIP to get started.
          </p>
          <button onClick={() => navigate('/upload')} className="btn-primary">
            Add Your First Repo
          </button>
        </div>
      ) : (
        <div className="grid gap-3">
          {repos.map(r => <RepoCard key={r.id} repo={r} />)}
        </div>
      )}
    </div>
  )
}
