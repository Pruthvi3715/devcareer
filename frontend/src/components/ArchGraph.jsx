import { useCallback, useMemo, useEffect, forwardRef } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'

const NODE_COLORS = {
  entryPoint: { border: '#2563EB', fill: '#EFF6FF', badge: 'ENTRY' },
  highImpact: { border: '#DC2626', fill: '#FEF2F2', badge: 'CHANGE RISK' },
  orphaned: { border: '#6B7280', fill: '#F9FAFB', badge: 'ORPHANED' },
  normal: { border: '#D1D5DB', fill: '#FFFFFF', badge: null },
  highlighted: { border: '#D97706', fill: '#FEF3C7', badge: null },
}

function normPath(s) {
  return String(s ?? '').replace(/\\/g, '/').trim()
}

/** Match module_summaries keys from API (mixed separators / basenames) to a graph node id. */
function pickModuleSummary(nodeId, summaries) {
  if (!summaries || typeof summaries !== 'object') return undefined
  const n = normPath(nodeId)
  if (summaries[n]) return summaries[n]
  if (summaries[nodeId]) return summaries[nodeId]
  const base = n.split('/').pop() || ''
  for (const [k, v] of Object.entries(summaries)) {
    const kn = normPath(k)
    if (kn === n) return v
    if (kn.split('/').pop() === base && base) return v
  }
  return undefined
}

function CustomNode({ data, selected }) {
  const safe = data ?? {}
  const { isOrphaned, changeRisk, isHighlighted, nodeType } = safe

  const getNodeStyle = () => {
    if (isHighlighted) {
      return {
        background: NODE_COLORS.highlighted.fill,
        border: `2px solid ${NODE_COLORS.highlighted.border}`,
        borderRadius: '8px',
        padding: '10px 15px',
        color: '#1F2937',
        fontSize: '12px',
        minWidth: '120px',
        textAlign: 'center',
      }
    }

    let colorSet = NODE_COLORS.normal
    if (nodeType === 'entry_point') colorSet = NODE_COLORS.entryPoint
    else if (changeRisk === 'HIGH') colorSet = NODE_COLORS.highImpact
    else if (isOrphaned) colorSet = NODE_COLORS.orphaned

    return {
      background: colorSet.fill,
      border: selected ? '2px solid #8B5CF6' : `1px solid ${colorSet.border}`,
      borderRadius: '8px',
      padding: '10px 15px',
      color: '#1F2937',
      fontSize: '12px',
      minWidth: '120px',
      textAlign: 'center',
    }
  }

  const nodeStyle = getNodeStyle()

  const getBadge = () => {
    if (isHighlighted) return null
    if (nodeType === 'entry_point') return NODE_COLORS.entryPoint.badge
    if (changeRisk === 'HIGH') return NODE_COLORS.highImpact.badge
    if (isOrphaned) return NODE_COLORS.orphaned.badge
    return null
  }

  const badge = getBadge()

  return (
    <div style={nodeStyle}>
      <Handle type="target" position={Position.Top} style={{ background: '#8B5CF6' }} />
      <div className="font-medium">{safe.label ?? '—'}</div>
      {safe.moduleSummary && (
        <div className="text-gray-500 text-xs mt-1">{safe.moduleSummary}</div>
      )}
      {badge && (
        <div className="flex gap-1 mt-2 justify-center">
          <span
            className="px-1.5 py-0.5 text-xs rounded"
            style={{
              background:
                NODE_COLORS[
                  nodeType === 'entry_point'
                    ? 'entryPoint'
                    : changeRisk === 'HIGH'
                      ? 'highImpact'
                      : 'orphaned'
                ].fill,
              color:
                NODE_COLORS[
                  nodeType === 'entry_point'
                    ? 'entryPoint'
                    : changeRisk === 'HIGH'
                      ? 'highImpact'
                      : 'orphaned'
                ].border,
            }}
          >
            {badge}
          </span>
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: '#8B5CF6' }} />
    </div>
  )
}

const nodeTypes = { customNode: CustomNode }

const EMPTY_GRAPH = { nodes: [], edges: [] }

function applyGridLayout(nodes) {
  if (!nodes.length) return nodes
  const allAtOrigin = nodes.every(
    (n) => (Number(n.position?.x) || 0) === 0 && (Number(n.position?.y) || 0) === 0
  )
  if (!allAtOrigin) return nodes
  const cols = Math.max(1, Math.ceil(Math.sqrt(nodes.length)))
  const gapX = 260
  const gapY = 130
  return nodes.map((n, i) => ({
    ...n,
    position: { x: (i % cols) * gapX, y: Math.floor(i / cols) * gapY },
  }))
}

function ArchGraphCanvas({
  archGraph = EMPTY_GRAPH,
  onNodeClick,
  highlightedNodes = [],
  selectedNodeId = null,
  focusKey = 0,
  moduleSummaries = null,
}) {
  const { fitView, getNode } = useReactFlow()

  const archSig = useMemo(() => {
    const raw = archGraph?.nodes
    if (!raw?.length) return 'empty'
    return `${raw.map((x) => normPath(x.id)).sort().join('|')}@${(archGraph?.edges || []).length}`
  }, [archGraph])

  const highlightSet = useMemo(() => {
    const set = new Set()
    for (const raw of highlightedNodes || []) {
      const s = String(raw)
      set.add(s)
      set.add(normPath(s))
    }
    return set
  }, [highlightedNodes])

  const selectedNorm = selectedNodeId ? normPath(selectedNodeId) : null

  const initialNodes = useMemo(() => {
    const rawNodes = archGraph?.nodes
    if (!rawNodes || rawNodes.length === 0) {
      return [
        {
          id: '1',
          type: 'customNode',
          position: { x: 250, y: 0 },
          data: { label: 'No data', moduleSummary: 'No architecture data available' },
        },
      ]
    }
    const out = []
    for (let i = 0; i < rawNodes.length; i++) {
      const node = rawNodes[i]
      const id = normPath(node?.id != null ? String(node.id) : `n-${i}`)
      const isEntry = Boolean(node.type === 'entry_point' || node.is_entry_point)
      const summaryFromGraph = node.module_summary
      const summaryFromReport = pickModuleSummary(id, moduleSummaries)
      out.push({
        id,
        type: 'customNode',
        position: { x: Number(node.x) || 0, y: Number(node.y) || 0 },
        selected: Boolean(selectedNorm && id === selectedNorm),
        data: {
          label:
            node.label != null
              ? String(node.label)
              : id.split('/').pop() || id.split('\\').pop() || id,
          moduleSummary: summaryFromGraph || summaryFromReport,
          isOrphaned: node.is_orphaned,
          changeRisk: node.change_risk || (node.in_degree > 3 ? 'HIGH' : 'LOW'),
          nodeType: isEntry ? 'entry_point' : node.type || 'module',
          isHighlighted: highlightSet.has(id) || highlightSet.has(normPath(id)),
        },
      })
    }
    return applyGridLayout(out)
  }, [archGraph, highlightSet, moduleSummaries, selectedNorm])

  const initialEdges = useMemo(() => {
    const rawEdges = archGraph?.edges
    if (!rawEdges || rawEdges.length === 0) return []
    const nodeIds = new Set(initialNodes.map((n) => n.id))
    return rawEdges
      .map((edge, i) => {
        const source = normPath(edge?.source != null ? String(edge.source) : '')
        const target = normPath(edge?.target != null ? String(edge.target) : '')
        if (!source || !target || !nodeIds.has(source) || !nodeIds.has(target)) return null
        return {
          id: edge.id != null ? String(edge.id) : `e-${source}-${target}-${i}`,
          source,
          target,
          animated: Boolean(edge.animated),
          style: { stroke: '#9CA3AF', strokeWidth: 1 },
          type: 'smoothstep',
        }
      })
      .filter(Boolean)
  }, [archGraph, initialNodes])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges, setNodes, setEdges])

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      try {
        if (selectedNorm) return
        if (!nodes.length) return
        fitView({ padding: 0.2, duration: 250, maxZoom: 1.35, minZoom: 0.2 })
      } catch {
        /* ignore */
      }
    })
    return () => cancelAnimationFrame(id)
  }, [archSig, selectedNorm, fitView, nodes.length])

  useEffect(() => {
    if (!selectedNorm) return
    const id = requestAnimationFrame(() => {
      try {
        if (!getNode(selectedNorm)) return
        fitView({
          nodes: [{ id: selectedNorm }],
          duration: 420,
          padding: 0.42,
          maxZoom: 1.55,
          minZoom: 0.12,
        })
      } catch {
        /* ignore */
      }
    })
    return () => cancelAnimationFrame(id)
  }, [selectedNorm, focusKey, getNode, fitView])

  const onNodeClickHandler = useCallback(
    (event, node) => {
      onNodeClick?.(node)
    },
    [onNodeClick]
  )

  return (
    <ReactFlow
      className="h-full w-full"
      style={{ width: '100%', height: '100%' }}
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClickHandler}
      nodeTypes={nodeTypes}
      fitView={false}
      minZoom={0.15}
      maxZoom={2}
      defaultViewport={{ x: 0, y: 0, zoom: 1 }}
    >
      <Background color="#E5E7EB" gap={20} />
      <Controls className="!bg-white !border-gray-200" />
      <MiniMap
        nodeColor={(node) => {
          if (node.data?.isHighlighted) return '#D97706'
          if (node.data?.changeRisk === 'HIGH') return '#DC2626'
          if (node.data?.isOrphaned) return '#6B7280'
          return '#8B5CF6'
        }}
        maskColor="rgba(255, 255, 255, 0.8)"
        className="!bg-gray-50"
      />
    </ReactFlow>
  )
}

const ArchGraph = forwardRef(function ArchGraph(
  {
    selectedNodeId,
    focusKey,
    moduleSummaries,
    ...rest
  },
  ref
) {
  return (
    <section
      ref={ref}
      id="arch-graph-export-root"
      className="relative h-full min-h-0 w-full min-w-0 bg-white"
      aria-label="Interactive code architecture graph. Use mouse or trackpad to pan and zoom; onboard steps in the sidebar list key files."
    >
      <div className="absolute inset-0 min-h-0 min-w-0">
        <ReactFlowProvider>
          <ArchGraphCanvas
            {...rest}
            selectedNodeId={selectedNodeId}
            focusKey={focusKey}
            moduleSummaries={moduleSummaries}
          />
        </ReactFlowProvider>
      </div>

      <div className="pointer-events-none absolute bottom-4 left-4 flex gap-4 text-xs" aria-hidden="true">
        <div className="flex items-center gap-1">
          <span className="h-3 w-3 rounded-full" style={{ background: '#2563EB' }} />
          Entry Point
        </div>
        <div className="flex items-center gap-1">
          <span className="h-3 w-3 rounded-full" style={{ background: '#DC2626' }} />
          High Impact
        </div>
        <div className="flex items-center gap-1">
          <span className="h-3 w-3 rounded-full" style={{ background: '#6B7280' }} />
          Orphaned
        </div>
        <div className="flex items-center gap-1">
          <span className="h-3 w-3 rounded-full" style={{ background: '#D1D5DB' }} />
          Normal
        </div>
      </div>
    </section>
  )
})

ArchGraph.displayName = 'ArchGraph'

export default ArchGraph
