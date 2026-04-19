import { useState } from 'react'

const roiConfig = {
  high: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  medium: { bg: 'bg-amber-100', text: 'text-amber-800', border: 'border-amber-300' },
  low: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300' }
}

export default function GapAnalysis({ gaps = [], onEvidenceClick }) {
  const [expandedIdx, setExpandedIdx] = useState(null)

  if (!gaps || gaps.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Career Gap Analysis</h3>
        <p className="text-gray-500">No significant gaps identified.</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">What's blocking your next level</h3>
        <p className="text-sm text-gray-500">Ranked by career impact • {gaps.length} gaps identified</p>
      </div>
      
      <div className="space-y-4">
        {gaps.map((gap, idx) => {
          const isExpanded = expandedIdx === idx
          const roi = gap.career_roi?.toLowerCase() || 'medium'
          const roiStyle = roiConfig[roi] || roiConfig.medium
          
          return (
            <div 
              key={idx} 
              className={`border rounded-lg transition-colors ${isExpanded ? 'border-gray-300' : 'border-gray-200'}`}
              data-gap={gap.name}
            >
              <button
                type="button"
                className="w-full p-4 cursor-pointer text-left"
                onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                aria-expanded={isExpanded}
                aria-controls={`gap-panel-${idx}`}
                id={`gap-header-${idx}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-sm font-medium">
                      {idx + 1}
                    </span>
                    <h4 className="text-gray-900 font-medium">{gap.gap}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${roiStyle.bg} ${roiStyle.text}`}>
                      {roi.toUpperCase()} ROI
                    </span>
                    <span className="text-gray-400" aria-hidden="true">{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>
              </button>

              {isExpanded && (
                <div id={`gap-panel-${idx}`} className="px-4 pb-4 border-t border-gray-100 pt-3" role="region" aria-labelledby={`gap-header-${idx}`}>
                  {gap.evidence && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1">Evidence:</p>
                      <p className="text-sm text-gray-700">{gap.evidence}</p>
                      {gap.citation && (
                        <button 
                          type="button"
                          onClick={(e) => { e.stopPropagation(); onEvidenceClick?.(gap.citation) }}
                          className="text-xs font-mono text-purple-600 hover:text-purple-800 mt-1 inline-block"
                        >
                          {gap.citation}
                        </button>
                      )}
                    </div>
                  )}
                  
                  {gap.fix && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1">How to fix:</p>
                      <p className="text-sm text-gray-700">{gap.fix}</p>
                    </div>
                  )}
                  
                  {gap.promotion_impact && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-xs text-green-700 font-medium mb-1">Promotion impact:</p>
                      <p className="text-sm text-green-800">{gap.promotion_impact}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}