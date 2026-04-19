import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

const ZONE_COLORS = {
  developing: '#DC2626',
  growing: '#D97706',
  competitive: '#2563EB',
  topTier: '#059669'
}

const roleConfig = {
  'Junior': { qualifying: { bg: 'bg-green-100', text: 'text-green-800' }, notQualifying: { bg: 'bg-gray-100', text: 'text-gray-400' } },
  'Mid-Level': { qualifying: { bg: 'bg-blue-100', text: 'text-blue-800' }, notQualifying: { bg: 'bg-gray-100', text: 'text-gray-400' } },
  'Senior': { qualifying: { bg: 'bg-purple-100', text: 'text-purple-800' }, notQualifying: { bg: 'bg-gray-100', text: 'text-gray-400' } },
  'Staff': { qualifying: { bg: 'bg-amber-100', text: 'text-amber-800' }, notQualifying: { bg: 'bg-gray-100', text: 'text-gray-400' } }
}

function getZone(percentile) {
  if (percentile <= 25) return { label: 'Developing', color: ZONE_COLORS.developing }
  if (percentile <= 50) return { label: 'Growing', color: ZONE_COLORS.growing }
  if (percentile <= 75) return { label: 'Competitive', color: ZONE_COLORS.competitive }
  return { label: 'Top Tier', color: ZONE_COLORS.topTier }
}

export default function PercentileCard({ 
  percentile, 
  languages = [], 
  yearsActive, 
  salaryUnlockSkills = [],
  qualifyingRoles = [],
  onSkillClick
}) {
  const [animated, setAnimated] = useState(false)
  const percentileNum = percentile || 0
  const zone = getZone(percentileNum)

  useEffect(() => {
    setTimeout(() => setAnimated(true), 300)
  }, [])

  const data = [
    { name: 'Above', value: percentileNum },
    { name: 'Below', value: 100 - percentileNum }
  ]

  const displayPercentile = animated ? percentileNum : 0

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Peer Ranking</h3>
      
      <div className="flex items-center justify-center mb-4">
        <div className="relative w-40 h-24" aria-hidden="true">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="100%"
                startAngle={180}
                endAngle={0}
                innerRadius={50}
                outerRadius={70}
                dataKey="value"
                stroke="none"
              >
                <Cell fill={zone.color} />
                <Cell fill="#E5E7EB" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="text-center mb-4">
        <p className="sr-only">Peer ranking: top {displayPercentile} percent, {zone.label} band.</p>
        <span className="text-4xl font-bold" style={{ color: zone.color }} aria-hidden="true">
          Top {displayPercentile}%
        </span>
        <p className="text-sm text-gray-500 mt-1" aria-hidden="true">{zone.label}</p>
        {yearsActive && (
          <p className="text-xs text-gray-400 mt-2">
            among {languages[0] || 'developers'} with {yearsActive} years experience
          </p>
        )}
      </div>

      {languages && languages.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 mb-2">Primary Languages</p>
          <div className="flex flex-wrap gap-1.5">
            {languages.map((lang) => (
              <span key={lang} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                {lang}
              </span>
            ))}
          </div>
        </div>
      )}

      {qualifyingRoles && qualifyingRoles.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 mb-2">Qualifies for:</p>
          <div className="flex flex-wrap gap-1.5">
            {qualifyingRoles.map((role) => {
              const config = roleConfig[role] || roleConfig['Mid-Level']
              return (
                <span 
                  key={role} 
                  className={`px-2.5 py-1 text-xs font-medium rounded-full ${config.qualifying.bg} ${config.qualifying.text}`}
                >
                  {role}
                </span>
              )
            })}
          </div>
        </div>
      )}

      {salaryUnlockSkills && salaryUnlockSkills.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="text-sm font-medium text-amber-800 mb-2">
            💰 Skills that unlock your next salary bracket
          </p>
          <div className="flex flex-wrap gap-1.5">
            {salaryUnlockSkills.map((skill) => (
              <button
                key={skill}
                type="button"
                onClick={() => onSkillClick?.(skill)}
                className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded hover:bg-amber-200 transition-colors"
                aria-label={onSkillClick ? `Show gap analysis for ${skill}` : undefined}
              >
                {skill}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}