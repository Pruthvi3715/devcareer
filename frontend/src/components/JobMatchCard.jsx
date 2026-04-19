export default function JobMatchCard({ job }) {
  const { title, company, match_score, url, location, salary_range } = job

  const scoreColor = match_score >= 80 ? 'text-green-400' : match_score >= 60 ? 'text-yellow-400' : 'text-gray-400'

  const label = `${title} at ${company}, ${match_score}% match`.trim()

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-purple-500/50 transition-colors"
      aria-label={label}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h4 className="text-white font-medium">{title}</h4>
          <p className="text-sm text-gray-400">{company}</p>
        </div>
        <span className={`text-lg font-bold ${scoreColor}`}>{match_score}%</span>
      </div>
      
      <div className="flex items-center gap-4 mt-3">
        {location && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            📍 {location}
          </span>
        )}
        {salary_range && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            💰 {salary_range}
          </span>
        )}
      </div>
      
      <div className="mt-3 text-xs text-purple-400">
        View Job →
      </div>
    </a>
  )
}