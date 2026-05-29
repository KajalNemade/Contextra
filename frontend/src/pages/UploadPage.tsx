import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { repoApi } from '../services/api'

type Tab = 'url' | 'zip'

export default function UploadPage() {
  const navigate = useNavigate()
  const [tab, setTab]         = useState<Tab>('url')
  const [url, setUrl]         = useState('')
  const [name, setName]       = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const go = (id: number) => navigate(`/repo/${id}`)

  const submitUrl = async () => {
    if (!url.trim()) return
    setLoading(true); setError('')
    try {
      const repo = await repoApi.create(url.trim(), name.trim() || undefined)
      go(repo.id)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to submit. Check the URL.')
    } finally {
      setLoading(false)
    }
  }

  const submitZip = async (file: File) => {
    if (!file.name.endsWith('.zip')) { setError('Only .zip files accepted'); return }
    setLoading(true); setError('')
    try {
      const repo = await repoApi.uploadZip(file)
      go(repo.id)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) submitZip(file)
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {/* Back */}
      <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm mb-6 flex items-center gap-1">
        ← Back to Repos
      </button>

      <h1 className="text-2xl font-bold text-white mb-2">Add Repository</h1>
      <p className="text-gray-400 text-sm mb-8">
        Paste a public GitHub URL or upload a ZIP. Your code stays local — nothing leaves your machine.
      </p>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800 rounded-lg p-1 w-fit mb-6">
        {(['url', 'zip'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setError('') }}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {t === 'url' ? '🔗 GitHub URL' : '📦 ZIP Upload'}
          </button>
        ))}
      </div>

      <div className="card">
        {tab === 'url' ? (
          <div className="space-y-4">
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">GitHub Repository URL</label>
              <input
                type="url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submitUrl()}
                placeholder="https://github.com/org/repo"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
                autoFocus
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">
                Display Name <span className="text-gray-600">(optional)</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="my-project"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
              />
            </div>
            <button onClick={submitUrl} disabled={loading || !url.trim()} className="btn-primary w-full py-3">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⟳</span> Submitting…
                </span>
              ) : 'Analyze Repository'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                dragOver ? 'border-brand-500 bg-brand-500/5' : 'border-gray-700 hover:border-gray-500'
              }`}
            >
              <div className="text-4xl mb-3">{dragOver ? '📂' : '📦'}</div>
              <p className="text-white font-medium mb-1">
                {dragOver ? 'Drop it!' : 'Drop ZIP here or click to browse'}
              </p>
              <p className="text-gray-500 text-sm">Max 500 files · 100k LOC per repo</p>
              <input
                ref={fileRef}
                type="file"
                accept=".zip"
                className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) submitZip(f) }}
              />
            </div>

            {loading && (
              <div className="text-center text-sm text-gray-400 animate-pulse">
                Uploading and extracting…
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-sm text-red-300">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Info cards */}
      <div className="mt-8 grid grid-cols-3 gap-3">
        {[
          { icon: '🔒', title: 'Secret Scanner', desc: 'API keys & tokens are detected and redacted before any AI sees your code.' },
          { icon: '🏠', title: '100% Local', desc: 'Parsing and search run on your machine. AI is optional and opt-in.' },
          { icon: '⚡', title: 'Fast Parse', desc: 'Tree-sitter parses 500 files in seconds. No cloud upload needed.' },
        ].map(c => (
          <div key={c.title} className="card text-center">
            <div className="text-2xl mb-2">{c.icon}</div>
            <div className="text-xs font-semibold text-white mb-1">{c.title}</div>
            <div className="text-xs text-gray-500">{c.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
