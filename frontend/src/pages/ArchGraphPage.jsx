import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useState, useMemo, useEffect, startTransition, useRef, useCallback } from 'react'
import ArchGraph from '../components/ArchGraph'
import axios from 'axios'
import html2canvas from 'html2canvas'
import API_BASE from '../utils/api'

/** Stable fallback — inline `{ nodes: [], edges: [] }` breaks ArchGraph memo/effects (new ref every render → update loop → blank screen). */
const EMPTY_ARCH_GRAPH = { nodes: [], edges: [] }

const EXAMPLE_QUERIES = [
  'Where is auth handled?',
  'What calls the database?',
  'What is the entry point?'
]

function normalizePath(p) {
  return String(p ?? '')
    .replace(/\\/g, '/')
    .trim()
}

/** Map NLQ / UI paths to a graph node id (handles slash style and basename fallbacks). */
function resolveGraphNodeId(raw, graphNodes) {
  const want = normalizePath(raw)
  if (!want) return null
  const nodes = graphNodes || []
  if (!nodes.length) return want
  const ids = nodes.map((n) => normalizePath(n.id))
  if (ids.includes(want)) return want
  const found = nodes.find((n) => {
    const id = normalizePath(n.id)
    return id === want || id.endsWith(`/${want}`) || want.endsWith(id)
  })
  if (found) return normalizePath(found.id)
  const wantBase = want.split('/').pop()
  const byBase = nodes.find((n) => normalizePath(n.id).split('/').pop() === wantBase)
  return byBase ? normalizePath(byBase.id) : want
}

function pickSummaryForPath(path, summaries) {
  if (!path || !summaries || typeof summaries !== 'object') return null
  const n = normalizePath(path)
  if (summaries[n]) return summaries[n]
  for (const [k, v] of Object.entries(summaries)) {
    const kn = normalizePath(k)
    if (kn === n) return v
    if (kn.split('/').pop() === n.split('/').pop() && n.split('/').pop()) return v
  }
  return null
}

export default function ArchGraphPage() {
  const { auditId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const repoName = searchParams.get('repo')
  
  const [selectedNode, setSelectedNode] = useState(null)
  const [report, setReport] = useState(null)
  const [nlqQuery, setNlqQuery] = useState('')
  const [nlqLoading, setNlqLoading] = useState(false)
  const [nlqResult, setNlqResult] = useState(null)
  const [nlqError, setNlqError] = useState(null)
  const [exportingGraph, setExportingGraph] = useState(false)
  const [graphExportError, setGraphExportError] = useState(null)
  const graphExportRef = useRef(null)
  const [focusKey, setFocusKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const stored = localStorage.getItem(`audit_${auditId}`)
        if (stored) {
          startTransition(() => {
            if (!cancelled) setReport(JSON.parse(stored))
          })
          return
        }
        const response = await axios.get(`${API_BASE}/report/${auditId}`, { timeout: 120000 })
        if (!cancelled && response.data) {
          const data = response.data
          setReport(data)
          try {
            localStorage.setItem(`audit_${auditId}`, JSON.stringify(data))
          } catch {
            /* ignore quota */
          }
        }
      } catch {
        if (!cancelled) setReport(null)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [auditId])

  const repoData = useMemo(() => {
    if (!report || !repoName) return null
    const repo = report.repo_scores?.find(r => r.repo_name === repoName)
    return repo?.arch_graph || null
  }, [report, repoName])

  const onboardingPath = useMemo(() => {
    if (!report || !repoName) return []
    const repo = report.repo_scores?.find(r => r.repo_name === repoName)
    return repo?.onboarding_path || []
  }, [report, repoName])

  const moduleSummaries = useMemo(() => {
    if (!report || !repoName) return {}
    const repo = report.repo_scores?.find(r => r.repo_name === repoName)
    return repo?.module_summaries || {}
  }, [report, repoName])

  const highlightedNodeIds = useMemo(() => {
    const raw = nlqResult?.relevant_nodes?.map((n) => n?.id).filter(Boolean) ?? []
    return raw
  }, [nlqResult])

  const graphNodes = repoData?.nodes ?? []

  const graphSelectedNodeId = useMemo(() => {
    const raw = selectedNode?.id || selectedNode?.data?.label
    if (!raw) return null
    return resolveGraphNodeId(raw, graphNodes)
  }, [selectedNode, graphNodes])

  const selectedSummary = useMemo(
    () => pickSummaryForPath(selectedNode?.id || selectedNode?.data?.label, moduleSummaries),
    [selectedNode, moduleSummaries]
  )

  const selectFileFromPath = useCallback(
    (path) => {
      const resolved = resolveGraphNodeId(path, graphNodes)
      setSelectedNode({ id: resolved, data: { label: resolved } })
      setFocusKey((k) => k + 1)
    },
    [graphNodes]
  )

  const handleNlqSearch = async (query) => {
    if (!query.trim()) return
    
    setNlqLoading(true)
    setNlqError(null)
    setNlqQuery(query)

    try {
      const response = await axios.get(`${API_BASE}/report/${auditId}/nlq`, {
        params: {
          query,
          ...(repoName ? { repo: repoName } : {}),
        },
      })
      setNlqResult(response.data)
    } catch (err) {
      setNlqError(err.response?.data?.detail || 'Query timed out. Try a simpler question.')
    } finally {
      setNlqLoading(false)
    }
  }

  const clearNlqSearch = () => {
    setNlqQuery('')
    setNlqResult(null)
    setNlqError(null)
  }

  const handleDownloadGraphJpeg = useCallback(async () => {
    const el = graphExportRef.current ?? document.getElementById('arch-graph-export-root')
    if (!el || exportingGraph) return
    setExportingGraph(true)
    setGraphExportError(null)
    try {
      const canvas = await html2canvas(el, {
        backgroundColor: '#ffffff',
        scale: Math.min(2, (typeof window !== 'undefined' && window.devicePixelRatio) || 2),
        useCORS: true,
        logging: false,
        foreignObjectRendering: true,
        scrollX: 0,
        scrollY: -window.scrollY,
      })
      const safeName = (repoName || auditId || 'graph').replace(/[^\w.-]+/g, '_')
      const link = document.createElement('a')
      link.download = `architecture-graph-${safeName}.jpeg`
      link.href = canvas.toDataURL('image/jpeg', 0.92)
      link.click()
    } catch {
      setGraphExportError('Could not export the graph. Try again, or zoom so the full diagram is visible.')
    } finally {
      setExportingGraph(false)
    }
  }, [auditId, repoName, exportingGraph])

  const nlqInputId = 'arch-nlq-query'

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <header className="border-b border-gray-200 bg-white px-4 py-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="Go back"
          >
            ← Back
          </button>
          <h1 className="text-lg font-semibold text-gray-900">
            Architecture Graph {repoName && `- ${repoName}`}
          </h1>
        </div>
        <button
          type="button"
          onClick={handleDownloadGraphJpeg}
          disabled={exportingGraph}
          className="shrink-0 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-800 shadow-sm hover:bg-gray-50 disabled:opacity-50"
        >
          {exportingGraph ? 'Exporting…' : 'Download graph (.jpeg)'}
        </button>
      </header>
      {graphExportError && (
        <p className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900" role="alert">
          {graphExportError}
        </p>
      )}

      <main id="main-content" className="flex min-h-0 flex-1 flex-row outline-none" tabIndex={-1}>
        <div
          className="relative min-h-0 min-w-0 flex-1 overflow-hidden bg-white"
          role="presentation"
        >
          <ArchGraph
            ref={graphExportRef}
            archGraph={repoData ?? EMPTY_ARCH_GRAPH}
            onNodeClick={setSelectedNode}
            highlightedNodes={highlightedNodeIds}
            selectedNodeId={graphSelectedNodeId}
            focusKey={focusKey}
            moduleSummaries={moduleSummaries}
          />
        </div>

        <aside className="w-80 border-l border-gray-200 bg-white p-4 overflow-y-auto" aria-label="Architecture sidebar">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Onboarding Path</h3>
          
          {onboardingPath.length > 0 ? (
            <ol className="space-y-3 list-none p-0 m-0">
              {onboardingPath.map((step, idx) => (
                <li key={idx}>
                  <button
                    type="button"
                    className={`w-full text-left p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedNode?.data?.label === step.file
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => selectFileFromPath(step.file)}
                    aria-pressed={normalizePath(selectedNode?.id || selectedNode?.data?.label) === normalizePath(step.file)}
                  >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-5 h-5 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xs" aria-hidden="true">
                      {idx + 1}
                    </span>
                    <span className="text-gray-900 text-sm font-medium break-all">{step.file}</span>
                  </div>
                  <p className="text-gray-500 text-xs">{step.reason}</p>
                  </button>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-gray-500 text-sm">No onboarding path available.</p>
          )}

          {selectedNode && moduleSummaries[selectedNode.data?.label] && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200" role="region" aria-label={`Summary for ${selectedNode.data?.label}`}>
              <h4 className="text-gray-900 font-medium mb-2">
                {selectedNode.data?.label}
              </h4>
              <p className="text-gray-600 text-sm">
                {moduleSummaries[selectedNode.data?.label]}
              </p>
            </div>
          )}

          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Ask about this codebase</h3>
            
            <div className="space-y-2 mb-3">
              {EXAMPLE_QUERIES.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleNlqSearch(q)}
                  className="block w-full text-left px-3 py-2 text-xs text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>

            <div className="flex gap-2 items-end">
              <div className="flex-1 min-w-0">
                <label htmlFor={nlqInputId} className="sr-only">
                  Ask a question about this codebase
                </label>
              <input
                id={nlqInputId}
                type="search"
                value={nlqQuery}
                onChange={(e) => setNlqQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleNlqSearch(nlqQuery)}
                placeholder="Ask a question..."
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                aria-describedby={nlqError ? 'nlq-error' : undefined}
              />
              </div>
              <button
                type="button"
                onClick={() => handleNlqSearch(nlqQuery)}
                disabled={nlqLoading}
                className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 shrink-0"
                aria-label={nlqLoading ? 'Searching' : 'Submit question'}
              >
                {nlqLoading ? '...' : '→'}
              </button>
            </div>

            {nlqError && (
              <p id="nlq-error" className="text-xs text-red-600 mt-2" role="alert">{nlqError}</p>
            )}

            {nlqResult && (
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <h4 className="text-sm font-medium text-amber-800 mb-2">Results:</h4>
                <ul className="space-y-2">
                  {nlqResult.relevant_nodes?.map((node, idx) => (
                    <li key={idx} className="text-sm text-amber-700">
                      <button
                        type="button"
                        onClick={() => setSelectedNode({ data: { label: node.id } })}
                        className="hover:underline"
                      >
                        {node.id}
                      </button>
                      {node.reason && <p className="text-xs text-amber-600">{node.reason}</p>}
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={clearNlqSearch}
                  className="text-xs text-purple-600 hover:text-purple-800 mt-2"
                >
                  Clear results
                </button>
              </div>
            )}
          </div>
        </aside>
      </main>
    </div>
  )
}