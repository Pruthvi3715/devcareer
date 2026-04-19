/**
 * Centralized API configuration.
 * 
 * In development:  falls back to http://localhost:8000
 * In production:   set VITE_API_URL in Vercel env vars to your deployed backend URL.
 *                  e.g. https://devcareer-api.onrender.com
 */
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default API_BASE
