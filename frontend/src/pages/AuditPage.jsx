import { useParams, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import LoadingPipeline from '../components/LoadingPipeline'
import useAuditPolling from '../hooks/useAuditPolling'
import VerdictBadge from '../components/VerdictBadge'
import RepoScoreCard from '../components/RepoScoreCard'
import PercentileCard from '../components/PercentileCard'
import GapAnalysis from '../components/GapAnalysis'
import JobMatchCard from '../components/JobMatchCard'
import CareerReport from '../components/CareerReport'
import UIAuditPanel from '../components/UIAuditPanel'
import ProfileIcon from '../components/ProfileIcon'
import { exportToPPT } from '../utils/pptExport'

export default function AuditPage() {
  const { auditId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [shareCopied, setShareCopied] = useState(false)

  const { progress, error } = useAuditPolling(auditId, (data) => {
    setReport(data)
    localStorage.setItem(`audit_${auditId}`, JSON.stringify(data))
  })

  const handleShare = async () => {
    const url = `${window.location.origin}/report/${auditId}`
    try {
      await navigator.clipboard.writeText(url)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <main id="main-content" className="outline-none" tabIndex={-1}>
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg max-w-lg" role="alert">
          <h2 className="text-xl font-semibold mb-2">Audit Failed</h2>
          <p>{error}</p>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Try Another Username
          </button>
        </div>
        </main>
      </div>
    )
  }

  if (!report) {
    return (
      <main id="main-content" className="min-h-screen outline-none" tabIndex={-1} aria-busy="true">
        <LoadingPipeline progress={progress} currentStage={Math.ceil((progress / 100) * 5) + 1} />
      </main>
    )
  }

  const { 
    activity_snapshot, 
    repo_scores = [], 
    career_verdict, 
    market_intel,
    ui_audit 
  } = report
  const rankingByRepo = new Map(
    (career_verdict?.portfolio_ranking || []).map((r) => [r.repo, r])
  )

  const reposWithRanking = repo_scores.map((r) => {
    const ranked = rankingByRepo.get(r.repo_name)
    return {
      ...r,
      action: ranked?.action || 'neutral',
      rank: ranked?.rank ?? null,
      reason: ranked?.reason || ''
    }
  })

  const sortedRepos = [...reposWithRanking].sort((a, b) => {
    // Prefer explicit rank from the verdict engine (1 = best)
    if (a.rank != null && b.rank != null) return a.rank - b.rank
    if (a.rank != null) return -1
    if (b.rank != null) return 1
    // Fallback: higher score first
    return (b.score || 0) - (a.score || 0)
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            type="button"
            className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent cursor-pointer border-0 bg-transparent p-0"
            onClick={() => navigate('/')}
            aria-label="DevCareer home"
          >
            DevCareer
          </button>
          <div className="flex gap-4 items-center">
            <button
              type="button"
              onClick={handleShare}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              aria-label={shareCopied ? 'Share link copied to clipboard' : 'Copy report share link'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              {shareCopied ? '✓ Copied!' : 'Share'}
            </button>
            <button
              type="button"
              onClick={() => exportToPPT(report, `career-report-${auditId}`)}
              className="px-3 py-1.5 text-sm bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
            >
              ⬇ Download PPT
            </button>
            <button
              type="button"
              onClick={() => navigate(`/report/${auditId}`)}
              className="px-3 py-1.5 text-sm text-purple-600 hover:text-purple-800 transition-colors"
            >
              View Report
            </button>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            >
              New Audit
            </button>
            <ProfileIcon />
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-7xl mx-auto px-4 py-8 outline-none" tabIndex={-1}>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Your Portfolio — Ranked by Impression</h1>
          <p className="text-sm text-gray-500">Ordered by how a recruiter would perceive your GitHub profile</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {career_verdict && (
              <VerdictBadge
                verdict={career_verdict.verdict}
                confidence={Math.round((career_verdict.confidence || 0) * 100)}
                roles={market_intel?.qualifying_roles}
                topEvidence={career_verdict.verdict_evidence}
                languages={activity_snapshot?.top_languages}
                yearsActive={activity_snapshot?.years_active}
                repoCount={repo_scores.length}
              />
            )}

            {sortedRepos.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Repository Analysis</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sortedRepos.map((repo) => (
                    <RepoScoreCard
                      key={repo.repo_name}
                      repo={repo}
                      onViewGraph={(r) => {
                        navigate(`/arch/${auditId}?repo=${encodeURIComponent(r.repo_name)}`)
                      }}
                    />
                  ))}
                </div>
              </div>
            )}

            {career_verdict?.roadmap_90_days && (
              <CareerReport
                roadmap={career_verdict.roadmap_90_days}
                resumeBullets={career_verdict.resume_bullets}
                onRepoClick={(repoName) => {
                  const element = document.getElementById(`repo-${repoName}`)
                  element?.scrollIntoView({ behavior: 'smooth' })
                }}
              />
            )}

            {career_verdict?.gap_analysis && (
              <GapAnalysis gaps={career_verdict.gap_analysis} />
            )}

            {ui_audit && <UIAuditPanel uiAudit={ui_audit} />}
          </div>

          <div className="space-y-6">
            {activity_snapshot && (
              <PercentileCard
                percentile={market_intel?.percentile}
                languages={activity_snapshot.top_languages}
                yearsActive={activity_snapshot?.years_active}
                salaryUnlockSkills={market_intel?.salary_unlock_skills}
                qualifyingRoles={market_intel?.qualifying_roles}
                onSkillClick={(skill) => {
                  const element = document.querySelector(`[data-gap="${skill}"]`)
                  element?.scrollIntoView({ behavior: 'smooth' })
                }}
              />
            )}

            {market_intel?.job_matches && market_intel.job_matches.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Jobs You Can Apply For Today</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Based on your detected stack: {activity_snapshot?.top_languages?.join(' · ')}
                </p>
                <div className="space-y-3">
                  {market_intel.job_matches.slice(0, 5).map((job, idx) => (
                    <JobMatchCard key={idx} job={job} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}