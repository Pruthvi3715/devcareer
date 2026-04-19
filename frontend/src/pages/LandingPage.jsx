import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import ProfileIcon from '../components/ProfileIcon'
import API_BASE from '../utils/api'

const EXAMPLE_USERS = ['demo', 'facebook', 'google', 'microsoft', 'vercel']

const ERROR_MESSAGES = {
  empty: 'Please enter a GitHub username.',
  not_found: 'GitHub profile not found. Check the username and try again.',
  no_repos: 'No public repositories found for this profile.',
  rate_limit: 'Too many requests. Please wait a minute and try again.',
  server_error: 'Something went wrong on our end. Please try again.'
}

export default function LandingPage() {
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim()) {
      setError(ERROR_MESSAGES.empty)
      return
    }

    setLoading(true)
    setError('')

    try {
      const cleanUsername = username.trim().replace(/^@/, '').replace(/^https?:\/\/github\.com\//, '')
      
      const response = await axios.post(`${API_BASE}/audit`, {
        github_username: cleanUsername
      })

      const { audit_id } = response.data
      navigate(`/audit/${audit_id}`)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail || ''
      
      if (status === 404 || detail.includes('not found')) {
        setError(ERROR_MESSAGES.not_found)
      } else if (detail.includes('no public repos')) {
        setError(ERROR_MESSAGES.no_repos)
      } else if (status === 429) {
        setError(ERROR_MESSAGES.rate_limit)
      } else {
        setError(ERROR_MESSAGES.server_error)
      }
      setLoading(false)
    }
  }

  const handleExampleClick = (user) => {
    setUsername(user)
    setError('')
  }

  const usernameInputId = 'github-username'
  const errorId = 'github-username-error'

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4 relative">
      {/* Profile icon at top right */}
      <div style={{ position: 'absolute', top: '16px', right: '24px', zIndex: 50 }}>
        <ProfileIcon />
      </div>
      <main id="main-content" className="max-w-2xl w-full outline-none" tabIndex={-1}>
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            DevCareer
          </h1>
          <p className="text-xl text-gray-600">
            Developer Career Intelligence System
          </p>
          <p className="mt-4 text-gray-500">
            Audit your code. Know your level.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4" aria-busy={loading} noValidate>
          <div className="relative">
            <label htmlFor={usernameInputId} className="sr-only">
              GitHub username or profile URL
            </label>
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none" aria-hidden="true">
              <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
              </svg>
            </div>
            <input
              id={usernameInputId}
              type="text"
              name="github_username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter GitHub username or profile URL"
              className="w-full bg-white border border-gray-300 rounded-lg py-4 pl-12 pr-4 text-lg placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors"
              disabled={loading}
              aria-invalid={error ? 'true' : 'false'}
              aria-describedby={error ? errorId : undefined}
            />
          </div>

          {error && (
            <div
              id={errorId}
              role="alert"
              className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username.trim()}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 text-lg"
            aria-busy={loading}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Starting Audit...
              </span>
            ) : (
              'Run Audit →'
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 mb-3">Try it with:</p>
          <div className="flex justify-center gap-3 flex-wrap">
            {EXAMPLE_USERS.map((user) => (
              <button
                key={user}
                onClick={() => handleExampleClick(user)}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
              >
                {user}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-12 text-center text-gray-400 text-sm">
          <p>DevClash 2026 • April 18-19, 2026</p>
        </div>
      </main>
    </div>
  )
}