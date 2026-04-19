import { useState } from 'react'

const severityConfig = {
  critical: { bg: 'bg-red-100', text: 'text-red-800', label: 'Critical', chipBg: 'bg-red-100', chipText: 'text-red-800' },
  major: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Major', chipBg: 'bg-amber-100', chipText: 'text-amber-800' },
  minor: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Minor', chipBg: 'bg-blue-100', chipText: 'text-blue-800' }
}

const scoreConfig = {
  excellent: { color: '#059669', label: 'Excellent' },
  good: { color: '#2563EB', label: 'Good' },
  fair: { color: '#D97706', label: 'Fair' },
  poor: { color: '#DC2626', label: 'Poor' }
}

function ScoreRing({ score }) {
  const getScoreConfig = () => {
    if (score >= 85) return scoreConfig.excellent
    if (score >= 65) return scoreConfig.good
    if (score >= 40) return scoreConfig.fair
    return scoreConfig.poor
  }
  const config = getScoreConfig()
  const circumference = 2 * Math.PI * 18
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div className="relative w-16 h-16">
      <svg className="w-16 h-16 transform -rotate-90" aria-hidden="true">
        <circle cx="32" cy="32" r="18" stroke="#E5E7EB" strokeWidth="4" fill="none" />
        <circle 
          cx="32" cy="32" r="18" 
          stroke={config.color} 
          strokeWidth="4" 
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold" style={{ color: config.color }} aria-label={`Score ${score} out of 100`}>
          {score}
        </span>
      </div>
    </div>
  )
}

function FindingRow({ finding }) {
  const severity = finding.severity?.toLowerCase() || 'minor'
  const config = severityConfig[severity] || severityConfig.minor
  const [showFix, setShowFix] = useState(false)

  return (
    <div className={`${config.bg} border border-gray-200 rounded-lg p-3 mb-2`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${config.chipBg} ${config.chipText}`}>
              {config.label}
            </span>
            {finding.category && (
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                {finding.category}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-700">{finding.finding}</p>
        </div>
      </div>
      {finding.file && (
        <p className="text-xs text-gray-500 mt-1 font-mono">
          {finding.file}{finding.lines?.length ? `:${finding.lines.join(',')}` : ''}
        </p>
      )}
      {finding.fix && (
        <button
          type="button"
          onClick={() => setShowFix(!showFix)}
          className="text-xs text-purple-600 hover:text-purple-800 mt-2 flex items-center gap-1"
          aria-expanded={showFix}
        >
          {showFix ? '▲ Hide fix' : '▼ Show fix'}
        </button>
      )}
      {showFix && finding.fix && (
        <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-800">
          <span className="font-medium">Fix:</span> {finding.fix}
        </div>
      )}
    </div>
  )
}

export default function RepoScoreCard({ repo, onViewGraph }) {
  const { 
    repo_name,
    score,
    findings = [],
    action = 'neutral',
    reason = ''
  } = repo

  const [expanded, setExpanded] = useState(false)
  const [showAnyway, setShowAnyway] = useState(false)

  const isHidden = action === 'hide' && !showAnyway

  const counts = findings.reduce(
    (acc, f) => {
      const sev = (f.severity || 'minor').toLowerCase()
      if (sev === 'critical') acc.critical += 1
      else if (sev === 'major') acc.major += 1
      else acc.minor += 1
      return acc
    },
    { critical: 0, major: 0, minor: 0 }
  )

  const getActionBadge = () => {
    switch (action) {
      case 'lead_with':
        return { label: '⭐ Lead with this', bg: 'bg-green-100', text: 'text-green-800', border: 'border-l-4 border-green-500' }
      case 'neutral':
        return { label: 'Solid addition', bg: 'bg-blue-100', text: 'text-blue-800', border: '' }
      case 'hide':
        return { label: '⚠ Consider hiding', bg: 'bg-red-100', text: 'text-red-800', border: '' }
      default:
        return null
    }
  }

  const actionBadge = getActionBadge()

  if (isHidden) {
    return (
      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-4 opacity-60">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-500">{repo_name}</h3>
            <p className="text-sm text-gray-400">This repo may hurt your portfolio</p>
          </div>
          <button
            type="button"
            onClick={() => setShowAnyway(true)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Show anyway ▾
          </button>
        </div>
      </div>
    )
  }

  return (
    <article
      className={`bg-white border border-gray-200 rounded-xl p-5 ${actionBadge?.border || ''} ${action === 'lead_with' ? 'ring-2 ring-green-400' : ''}`}
      id={`repo-${repo_name}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-semibold text-gray-900">{repo_name}</h3>
            {actionBadge && (
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${actionBadge.bg} ${actionBadge.text}`}>
                {actionBadge.label}
              </span>
            )}
          </div>
          {reason && (
            <p className="text-xs text-gray-400 italic mt-1">{reason}</p>
          )}
        </div>
        <ScoreRing score={score} />
      </div>

      {(counts.critical > 0 || counts.major > 0 || counts.minor > 0) ? (
        <div className="flex gap-3 mb-3 flex-wrap">
          {counts.critical > 0 && (
            <span className="flex items-center gap-1 text-sm text-red-700">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              {counts.critical} Critical
            </span>
          )}
          {counts.major > 0 && (
            <span className="flex items-center gap-1 text-sm text-amber-700">
              <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
              {counts.major} Major
            </span>
          )}
          {counts.minor > 0 && (
            <span className="flex items-center gap-1 text-sm text-blue-700">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              {counts.minor} Minor
            </span>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-2 text-green-600 text-sm mb-3">
          <span>✓</span> No issues found
        </div>
      )}

      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="text-sm text-purple-600 hover:text-purple-800 flex items-center gap-1 mb-3"
        aria-expanded={expanded}
      >
        {expanded ? '▲ Hide findings' : `▼ View ${findings.length} findings`}
      </button>

      {expanded && findings.length > 0 && (
        <div className="border-t border-gray-200 pt-3">
          <div className="max-h-64 overflow-y-auto">
            {findings.map((finding, idx) => (
              <FindingRow key={idx} finding={finding} />
            ))}
          </div>
        </div>
      )}

      {onViewGraph && (
        <button
          type="button"
          onClick={() => onViewGraph(repo)}
          className="mt-3 w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors"
        >
          View full graph →
        </button>
      )}
    </article>
  )
}