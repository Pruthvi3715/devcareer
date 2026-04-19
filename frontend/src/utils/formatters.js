export function formatPercentile(value) {
  if (value == null) return 'N/A'
  return `${Math.round(value)}%`
}

export function formatScore(value) {
  if (value == null) return 'N/A'
  if (value >= 80) return { text: `${value}`, color: 'text-green-400' }
  if (value >= 60) return { text: `${value}`, color: 'text-yellow-400' }
  return { text: `${value}`, color: 'text-red-400' }
}

export function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

export function formatRelativeTime(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`
  return `${Math.floor(diffDays / 365)} years ago`
}

export function formatLanguage(language) {
  if (!language) return 'Unknown'
  return language
}

export function formatFileSize(bytes) {
  if (bytes == null) return 'N/A'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

export function formatNumber(value) {
  if (value == null) return '0'
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
  return value.toString()
}