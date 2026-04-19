import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import API_BASE from '../utils/api'

export default function useAuditPolling(auditId, onComplete) {
  const [status, setStatus] = useState(null)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)
  const intervalRef = useRef(null)
  const onCompleteRef = useRef(onComplete)

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    if (!auditId) return

    const pollStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/report/${auditId}/status`)
        const { status: currentStatus, progress: currentProgress } = response.data
        
        setStatus(currentStatus)
        setProgress(currentProgress)

        if (currentStatus === 'done') {
          clearInterval(intervalRef.current)
          
          const reportResponse = await axios.get(`${API_BASE}/report/${auditId}`)
          setReport(reportResponse.data)
          onCompleteRef.current?.(reportResponse.data)
        } else if (currentStatus === 'failed' || currentStatus === 'error') {
          clearInterval(intervalRef.current)
          setError(response.data?.message || 'Audit failed. Please try again.')
        }
      } catch (err) {
        clearInterval(intervalRef.current)
        setError(err.response?.data?.detail || 'Failed to fetch audit status')
      }
    }

    pollStatus()
    intervalRef.current = setInterval(pollStatus, 2000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [auditId])

  return { status, progress, error, report }
}