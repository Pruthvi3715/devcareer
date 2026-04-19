import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect, startTransition } from 'react'
import CareerReport from '../components/CareerReport'
import GapAnalysis from '../components/GapAnalysis'
import VerdictBadge from '../components/VerdictBadge'
import ProfileIcon from '../components/ProfileIcon'
import { exportToPDF } from '../utils/pdfExport'
import { exportToPPT } from '../utils/pptExport'

export default function CareerReportPage() {
  const { auditId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)

  useEffect(() => {
    const stored = localStorage.getItem(`audit_${auditId}`)
    startTransition(() => {
      setReport(stored ? JSON.parse(stored) : null)
    })
  }, [auditId])

  const handleExport = async () => {
    const element = document.getElementById('career-report-content')
    if (element) {
      await exportToPDF(element, `career-report-${auditId}`)
    }
  }

  const handlePPTExport = async () => {
    if (report) {
      await exportToPPT(report, `career-report-${auditId}`)
    }
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <main id="main-content" className="outline-none" tabIndex={-1}>
          <p className="text-gray-500" role="status" aria-live="polite">
            Loading report...
          </p>
        </main>
      </div>
    )
  }

  const { career_verdict, market_intel } = report

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            type="button"
            className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent cursor-pointer border-0 bg-transparent p-0"
            onClick={() => navigate('/')}
            aria-label="DevCareer home"
          >
            DevCareer
          </button>
          <div className="flex gap-4 items-center">
            <button
              type="button"
              onClick={handlePPTExport}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors text-sm"
            >
              ⬇ Download PPT
            </button>
            <button
              type="button"
              onClick={handleExport}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm"
            >
              Export PDF
            </button>
            <button
              type="button"
              onClick={() => navigate(`/audit/${auditId}`)}
              className="text-gray-400 hover:text-white transition-colors text-sm"
            >
              View Dashboard
            </button>
            <ProfileIcon />
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-4xl mx-auto px-4 py-8 outline-none" tabIndex={-1}>
        <div id="career-report-content">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Career Report</h1>
          <p className="text-gray-400">
            Generated on {new Date().toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>

        {career_verdict && (
          <VerdictBadge
            verdict={career_verdict.verdict}
            confidence={Math.round((career_verdict.confidence || 0) * 100)}
            roles={market_intel?.qualifying_roles}
            topEvidence={career_verdict.verdict_evidence}
          />
        )}

        <div className="mt-8">
          {career_verdict?.roadmap_90_days && (
            <CareerReport
              roadmap={career_verdict.roadmap_90_days}
              resumeBullets={career_verdict.resume_bullets}
            />
          )}
        </div>

        {career_verdict?.gap_analysis && (
          <div className="mt-8">
            <GapAnalysis gaps={career_verdict.gap_analysis} />
          </div>
        )}

        {market_intel && (
          <div className="mt-8 bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Market Position</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-400 text-sm">Percentile Ranking</p>
                <p className="text-2xl font-bold text-purple-400">{market_intel.percentile}%</p>
              </div>
              {market_intel.salary_unlock_skills && market_intel.salary_unlock_skills.length > 0 && (
                <div>
                  <p className="text-gray-400 text-sm">Next Bracket Skills</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {market_intel.salary_unlock_skills.map((skill) => (
                      <span key={skill} className="text-sm text-gray-300">{skill}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        </div>
      </main>
    </div>
  )
}