import { useCallback, useMemo } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/base.css'
import type { GraphData } from '../types/api'
import { LANG_COLORS } from '../utils/constants'

interface Props {
  data: GraphData
  onNodeClick?: (nodeId: string) => void
}

const LAYER_X: Record<string, number> = {
  file:   0,
  module: 600,
}

function buildLayout(graphData: GraphData): { nodes: Node[]; edges: Edge[] } {
  // Group nodes by language for positioning
  const fileNodes   = graphData.nodes.filter(n => n.type === 'file')
  const moduleNodes = graphData.nodes.filter(n => n.type === 'module')

  const nodes: Node[] = []

  fileNodes.forEach((n, i) => {
    const lang  = n.language ?? 'other'
    const color = LANG_COLORS[lang] ?? '#8b949e'
    nodes.push({
      id: n.id,
      position: { x: (i % 5) * 220, y: Math.floor(i / 5) * 90 },
      data: {
        label: (
          <div className="text-xs">
            <div className="font-medium truncate max-w-[160px]" title={n.id}>
              {n.id.split('/').pop()}
            </div>
            <div className="text-gray-400">{n.loc ? `${n.loc} LOC` : lang}</div>
          </div>
        ),
      },
      style: {
        background: '#1f2937',
        border: `1.5px solid ${color}`,
        borderRadius: 8,
        padding: '6px 10px',
        color: '#e5e7eb',
        fontSize: 12,
        minWidth: 160,
      },
    })
  })

  moduleNodes.forEach((n, i) => {
    nodes.push({
      id: n.id,
      position: { x: 1200 + (i % 3) * 180, y: i * 60 },
      data: { label: <div className="text-xs text-gray-400 truncate max-w-[140px]">{n.id}</div> },
      style: {
        background: '#111827',
        border: '1px dashed #374151',
        borderRadius: 6,
        padding: '4px 8px',
        color: '#6b7280',
        fontSize: 11,
        minWidth: 120,
      },
    })
  })

  const edges: Edge[] = graphData.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.source,
    target: e.target,
    markerEnd: { type: MarkerType.ArrowClosed, color: '#4b5563' },
    style: { stroke: '#4b5563', strokeWidth: 1 },
    animated: false,
  }))

  return { nodes, edges }
}

export default function GraphCanvas({ data, onNodeClick }: Props) {
  const { nodes: initNodes, edges: initEdges } = useMemo(() => buildLayout(data), [data])
  const [nodes, , onNodesChange] = useNodesState(initNodes)
  const [edges, , onEdgesChange] = useEdgesState(initEdges)

  const handleNodeClick = useCallback((_: any, node: Node) => {
    onNodeClick?.(node.id)
  }, [onNodeClick])

  return (
    <div className="w-full h-full bg-gray-950 rounded-xl overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#1f2937" gap={24} />
        <Controls className="!bg-gray-800 !border-gray-700" />
        <MiniMap
          nodeColor={n => {
            const lang = (n.data as any)?.language ?? 'other'
            return LANG_COLORS[lang] ?? '#374151'
          }}
          className="!bg-gray-900 !border-gray-700"
        />
      </ReactFlow>
    </div>
  )
}
