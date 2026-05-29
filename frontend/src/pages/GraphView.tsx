import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { graphApi } from '../services/api'
import type { GraphResponse } from '../types/api'
import GraphCanvas from '../components/GraphCanvas'

export default function GraphView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [data, setData] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const [impact, setImpact] = useState<any | null>(null)
  const [impactLoading, setImpactLoading] = useState(false)

  useEffect(() => {
    graphApi
      .get(Number(id))
      .then(setData)
      .catch((e) =>
        setError(e?.response?.data?.detail ?? 'Failed to load graph')
      )
      .finally(() => setLoading(false))
  }, [id])

  const handleNodeClick = async (nodeId: string) => {
    setSelected(nodeId)
    setImpactLoading(true)

    try {
      const result = await graphApi.impact(Number(id), nodeId)
      setImpact(result)
    } catch {
      setImpact(null)
    } finally {
      setImpactLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <span className="animate-spin mr-2">⟳</span>
        Building graph…
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="card border-red-800 text-red-400 max-w-md">
          <p className="font-medium mb-1">Cannot load graph</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-8 text-gray-400">
        No graph data available
      </div>
    )
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 relative">

        <div className="absolute top-4 left-4 z-10 flex gap-2">
          <button
            onClick={() => navigate(`/repo/${id}`)}
            className="bg-gray-800 border border-gray-700 text-gray-300 hover:text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
          >
            ← Back
          </button>

          <div className="bg-gray-800 border border-gray-700 text-xs px-3 py-1.5 rounded-lg text-gray-400">
            {data?.stats?.total_nodes ?? 0} nodes ·{' '}
            {data?.stats?.total_edges ?? 0} edges
          </div>

          {(data?.circular_dependencies?.length ?? 0) > 0 && (
            <div className="bg-red-900/60 border border-red-700 text-xs px-3 py-1.5 rounded-lg text-red-300">
              ⚠️ {data.circular_dependencies.length} circular dep
              {data.circular_dependencies.length > 1 ? 's' : ''}
            </div>
          )}
        </div>

        <GraphCanvas
          data={data?.graph ?? { nodes: [], edges: [] }}
          onNodeClick={handleNodeClick}
        />
      </div>

      <aside className="w-72 bg-gray-900 border-l border-gray-800 overflow-y-auto flex-shrink-0">
        <div className="p-4 border-b border-gray-800">
          <h2 className="font-semibold text-white text-sm">
            Dependency Graph
          </h2>
          <p className="text-gray-500 text-xs mt-0.5">
            Click any node for impact analysis
          </p>
        </div>

        {selected && (
          <div className="p-4 border-b border-gray-800">
            <div className="text-xs text-gray-500 mb-1">Selected</div>

            <div className="text-xs text-brand-400 font-mono break-all">
              {selected}
            </div>

            {impactLoading ? (
              <div className="mt-3 text-xs text-gray-500 animate-pulse">
                Running impact analysis…
              </div>
            ) : impact ? (
              <div className="mt-3">
                <div className="text-xs text-gray-500 mb-1">
                  Impact:{' '}
                  <span className="text-white">
                    {impact?.affected_count ?? 0} files affected
                  </span>
                </div>

                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {(impact?.affected_files ?? [])
                    .slice(0, 15)
                    .map((f: string, i: number) => (
                      <div
                        key={i}
                        className="text-xs text-gray-400 font-mono truncate"
                      >
                        {f}
                      </div>
                    ))}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </aside>
    </div>
  )
}