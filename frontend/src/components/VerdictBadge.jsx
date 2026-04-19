import { useState } from 'react'

const verdictConfig = {
  junior: {
    label: 'Junior',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-800',
    icon: '🌱'
  },
  mid: {
    label: 'Mid-Level',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    icon: '🚀'
  },
  senior: {
    label: 'Senior',
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-800',
    icon: '⭐'
  },
  staff: {
    label: 'Staff',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    text: 'text-purple-800',
    icon: '👑'
  }
}

function CodePill({ text }) {
  const codeMatch = text.match(/(.+):(\d+)/)
  if (codeMatch) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 bg-gray-200 text-gray-800 text-xs font-mono rounded">
        {codeMatch[1]}:<span className="font-bold">{codeMatch[2]}</span>
      </span>
    )
  }
  return <span className="text-sm text-gray-600">{text}</span>
}

export default function VerdictBadge({ 
  verdict, 
  confidence, 
  roles, 
  topEvidence = [],
  languages = [],
  yearsActive,
  repoCount,
  onEvidenceClick
}) {
  const config = verdictConfig[verdict?.toLowerCase()] || verdictConfig.mid
  const [showEvidence, setShowEvidence] = useState(false)

  const renderEvidenceWithCode = (evidence) => {
    const parts = evidence.split(/(:\d+)/g)
    return (
      <span>
        {parts.map((part, i) => {
          if (part.match(/:\d+/)) {
            return (
              <span key={i} className="inline-flex items-center px-1.5 py-0.5 bg-gray-200 text-gray-800 text-xs font-mono rounded mx-0.5">
                {part}
              </span>
            )
          }
          return <span key={i}>{part}</span>
        })}
      </span>
    )
  }

  return (
    <div className={`${config.bg} border ${config.border} rounded-xl p-6`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl" aria-hidden="true">{config.icon}</span>
          <div>
            <h3 className={`text-xl font-bold ${config.text}`}>
              {config.label} Developer
            </h3>
            <p className="text-sm text-gray-500">
              Confidence: {confidence}%
            </p>
            <div
              className="w-24 h-1 bg-gray-200 rounded-full mt-2 overflow-hidden"
              role="progressbar"
              aria-valuenow={confidence}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Confidence"
            >
              <div 
                className={`h-full ${config.text.replace('text-', 'bg-')}`}
                style={{ width: `${confidence}%`, transition: 'width 0.4s ease-in' }}
              />
            </div>
          </div>
        </div>
        {confidence >= 80 && (
          <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
            High Confidence
          </span>
        )}
      </div>

      {roles && roles.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className="text-sm text-gray-500">Qualifies for:</span>
          {roles.map((role) => (
            <span
              key={role}
              className="px-2.5 py-1 bg-white border border-gray-200 text-gray-700 text-xs font-medium rounded-full"
            >
              {role}
            </span>
          ))}
        </div>
      )}

      {languages && languages.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {languages.map((lang) => (
            <span 
              key={lang} 
              className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs rounded-md"
            >
              {lang}
            </span>
          ))}
        </div>
      )}

      {(yearsActive || repoCount) && (
        <div className="text-sm text-gray-500 mb-4">
          {yearsActive && <span>{yearsActive} years active</span>}
          {yearsActive && repoCount && <span> · </span>}
          {repoCount && <span>{repoCount} repos analysed</span>}
        </div>
      )}

      {topEvidence && topEvidence.length > 0 && (
        <div className="border-t border-gray-200 pt-4">
          <button
            type="button"
            onClick={() => setShowEvidence(!showEvidence)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
            aria-expanded={showEvidence}
          >
            <span>View Evidence ({topEvidence.length})</span>
            <span className={`transform transition-transform ${showEvidence ? 'rotate-180' : ''}`} aria-hidden="true">
              ▾
            </span>
          </button>
          
          {showEvidence && (
            <div className="mt-3 space-y-2">
              {topEvidence.slice(0, 5).map((evidence, idx) =>
                onEvidenceClick ? (
                  <button
                    key={idx}
                    type="button"
                    className="flex items-start gap-2 p-2 bg-white rounded-lg cursor-pointer hover:bg-gray-50 w-full text-left"
                    onClick={() => onEvidenceClick(evidence)}
                  >
                    <span className="text-purple-600 text-sm font-medium" aria-hidden="true">{idx + 1}.</span>
                    <span className="text-sm text-gray-700">{renderEvidenceWithCode(evidence)}</span>
                  </button>
                ) : (
                  <div 
                    key={idx} 
                    className="flex items-start gap-2 p-2 bg-white rounded-lg"
                  >
                    <span className="text-purple-600 text-sm font-medium">{idx + 1}.</span>
                    <span className="text-sm text-gray-700">{renderEvidenceWithCode(evidence)}</span>
                  </div>
                )
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}