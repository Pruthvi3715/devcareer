function getMetricColor(value, type) {
  const thresholds = {
    lcp: { good: 2500, poor: 4000 },
    fcp: { good: 1800, poor: 3000 },
    tti: { good: 3800, poor: 7300 },
    inp: { good: 200, poor: 200 },
    fps: { good: 55, poor: 30 }
  }
  
  const t = thresholds[type]
  if (!t) return 'text-gray-700'
  
  if (type === 'fps') {
    if (value >= t.good) return 'text-green-600'
    if (value >= t.poor) return 'text-amber-600'
    return 'text-red-600'
  }
  
  if (value <= t.good) return 'text-green-600'
  if (value <= t.poor) return 'text-amber-600'
  return 'text-red-600'
}

function getMetricLabel(value, type) {
  if (type === 'fps') {
    if (value >= 55) return 'Good'
    if (value >= 30) return 'Needs Improvement'
    return 'Poor'
  }
  
  const thresholds = {
    lcp: { good: 2500, poor: 4000 },
    fcp: { good: 1800, poor: 3000 },
    tti: { good: 3800, poor: 7300 },
    inp: { good: 200, poor: 200 }
  }
  
  const t = thresholds[type]
  if (!t) return ''
  
  if (value <= t.good) return 'Good'
  if (value <= t.poor) return 'Needs Improvement'
  return 'Poor'
}

function StatCard({ label, value, unit, type, subLabel }) {
  const colorClass = getMetricColor(value, type)
  const statusLabel = getMetricLabel(value, type)
  
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-xl font-bold ${colorClass}`}>
        {value}{unit}
      </p>
      {statusLabel && (
        <p className={`text-xs ${colorClass}`}>{statusLabel}</p>
      )}
      {subLabel && (
        <p className="text-xs text-gray-400 mt-1">{subLabel}</p>
      )}
    </div>
  )
}

function AccessibilityGauge({ score }) {
  const getColor = () => {
    if (score >= 90) return '#059669'
    if (score >= 50) return '#D97706'
    return '#DC2626'
  }
  
  const circumference = 2 * Math.PI * 18
  const progress = (score / 100) * circumference
  
  return (
    <div className="relative w-24 h-24">
      <svg className="w-24 h-24 transform -rotate-90" aria-hidden="true">
        <circle cx="48" cy="48" r="18" stroke="#E5E7EB" strokeWidth="4" fill="none" />
        <circle 
          cx="48" cy="48" r="18" 
          stroke={getColor()} 
          strokeWidth="4" 
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold" style={{ color: getColor() }} aria-label={`${score} out of 100`}>
          {score}
        </span>
      </div>
    </div>
  )
}

export default function UIAuditPanel({ uiAudit }) {
  if (!uiAudit) return null

  const { responsiveness, accessibility, load_times, animation: animData, interaction } = uiAudit

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mt-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6">Live App Audit</h3>

      {responsiveness && responsiveness.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Responsiveness</h4>
          <div className="grid grid-cols-3 gap-3">
            {responsiveness.map((breakpoint, idx) => (
              <div 
                key={idx} 
                className={`border-2 rounded-lg p-2 ${
                  breakpoint.pass ? 'border-green-400 bg-green-50' : 'border-red-400 bg-red-50'
                }`}
              >
                <p className="text-xs font-medium text-center mb-2">{breakpoint.breakpoint}px</p>
                {breakpoint.screenshot_url ? (
                  <img 
                    src={breakpoint.screenshot_url} 
                    alt={`${breakpoint.breakpoint}px view`}
                    className="w-full h-auto rounded"
                  />
                ) : (
                  <div className="bg-gray-200 h-20 flex items-center justify-center text-xs text-gray-500">
                    No screenshot
                  </div>
                )}
                <p className={`text-xs text-center mt-2 font-medium ${
                  breakpoint.pass ? 'text-green-600' : 'text-red-600'
                }`}>
                  {breakpoint.pass ? '✓ Pass' : '✗ Fail'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {accessibility && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Accessibility</h4>
          <div className="flex items-center gap-4">
            <AccessibilityGauge score={accessibility.score} />
            <div>
              <p className="text-sm text-gray-600">WCAG 2.1 Score</p>
              {accessibility.violations && accessibility.violations.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-purple-600 cursor-pointer">
                    View {accessibility.violations.length} violations
                  </summary>
                  <ul className="mt-2 text-xs text-gray-600">
                    {accessibility.violations.slice(0, 5).map((v, i) => (
                      <li key={i} className="mb-1">• {v}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        </div>
      )}

      {load_times && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Core Web Vitals</h4>
          <div className="grid grid-cols-3 gap-3">
            <StatCard 
              label="LCP" 
              value={load_times.lcp_ms} 
              unit="ms" 
              type="lcp"
              subLabel="Largest Contentful Paint"
            />
            <StatCard 
              label="FCP" 
              value={load_times.fcp_ms} 
              unit="ms" 
              type="fcp"
              subLabel="First Contentful Paint"
            />
            <StatCard 
              label="TTI" 
              value={load_times.tti_ms} 
              unit="ms" 
              type="tti"
              subLabel="Time to Interactive"
            />
          </div>
          {load_times.performance_score && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg flex items-center justify-between">
              <span className="text-sm text-gray-600">Performance Score</span>
              <span className={`text-lg font-bold ${getMetricColor(load_times.performance_score, 'fps')}`}>
                {load_times.performance_score}/100
              </span>
            </div>
          )}
        </div>
      )}

      {animData && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Animation</h4>
          <div className="grid grid-cols-2 gap-3">
            <StatCard 
              label="Avg FPS" 
              value={animData.avg_fps} 
              unit="" 
              type="fps"
            />
            <StatCard 
              label="Frame Drops" 
              value={animData.frame_drop_pct} 
              unit="%" 
              type="fps"
            />
          </div>
        </div>
      )}

      {interaction && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Interaction</h4>
          <StatCard 
            label="INP" 
            value={interaction.inp_ms} 
            unit="ms" 
            type="inp"
            subLabel="Interaction to Next Paint"
          />
        </div>
      )}
    </div>
  )
}