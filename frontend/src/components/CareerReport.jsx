import { useState } from 'react'

export default function CareerReport({ 
  roadmap = [], 
  resumeBullets = [],
  onRepoClick
}) {
  const [copiedIdx, setCopiedIdx] = useState(null)

  const copyToClipboard = async (text, idx) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIdx(idx)
      setTimeout(() => setCopiedIdx(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const copyAllBullets = async () => {
    const allBullets = resumeBullets.map(b => `• ${b.rewritten}`).join('\n')
    try {
      await navigator.clipboard.writeText(allBullets)
    } catch (err) {
      console.error('Failed to copy all:', err)
    }
  }

  const totalHours = roadmap.reduce((sum, w) => sum + (w.hours || 0), 0)

  return (
    <div className="space-y-8">
      {roadmap && roadmap.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="mb-4">
            <h3 className="text-xl font-bold text-gray-900">Your 90-Day Roadmap</h3>
            <p className="text-sm text-gray-500">Ordered by career impact</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {roadmap.map((week, idx) => (
              <div 
                key={idx} 
                className={`bg-gray-50 rounded-lg p-4 border ${
                  idx === 0 ? 'border-purple-400 ring-2 ring-purple-200' : 'border-gray-200'
                }`}
              >
                {idx === 0 && (
                  <span className="text-xs font-medium text-purple-600 mb-2 block">Start here</span>
                )}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-purple-600 text-sm font-semibold">Week {week.week}</span>
                  {week.hours && (
                    <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                      ~{week.hours}h
                    </span>
                  )}
                </div>
                <h4 className="text-gray-900 font-medium text-sm mb-1">{week.focus}</h4>
                <p className="text-gray-600 text-xs">{week.action}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 text-sm text-gray-500 text-center">
            Estimated total effort: ~{totalHours} hours over 90 days
          </div>
        </div>
      )}

      {resumeBullets && resumeBullets.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900">Resume Rewrite</h3>
              <p className="text-sm text-gray-500">Based on what your code actually shows</p>
            </div>
            <button
              type="button"
              onClick={copyAllBullets}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors"
            >
              Copy all rewrites
            </button>
          </div>

          <div className="space-y-4">
            {resumeBullets.map((bullet, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden flex">
                <div className="flex-1 bg-red-50 p-4 border-r border-gray-200">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-red-600">❌ Self-reported</span>
                  </div>
                  <p className="text-gray-500 line-through text-sm">{bullet.original_claim}</p>
                  {bullet.repo && (
                    <button 
                      type="button"
                      onClick={() => onRepoClick?.(bullet.repo)}
                      className="text-xs text-gray-400 hover:text-purple-600 mt-2"
                      aria-label={`Jump to repository ${bullet.repo}`}
                    >
                      From: {bullet.repo}
                    </button>
                  )}
                </div>
                <div className="flex-1 bg-green-50 p-4 relative">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-green-600">✓ Evidence-based</span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(bullet.rewritten, idx)}
                      className="text-xs text-purple-600 hover:text-purple-800"
                      aria-label={copiedIdx === idx ? `Copied improved bullet ${idx + 1}` : `Copy improved resume bullet ${idx + 1}`}
                    >
                      {copiedIdx === idx ? '✓ Copied!' : 'Copy'}
                    </button>
                  </div>
                  <p className="text-gray-800 text-sm">{bullet.rewritten}</p>
                  {bullet.repo && (
                    <button 
                      type="button"
                      onClick={() => onRepoClick?.(bullet.repo)}
                      className="text-xs text-gray-400 hover:text-purple-600 mt-2"
                      aria-label={`Jump to repository ${bullet.repo}`}
                    >
                      From: {bullet.repo}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}