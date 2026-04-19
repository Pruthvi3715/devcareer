import PptxGenJS from 'pptxgenjs'

/**
 * Generate a PowerPoint presentation from audit report data.
 * Uses pptxgenjs to create slides for each major section.
 */
export async function exportToPPT(report, filename = 'career-report') {
  const pptx = new PptxGenJS()
  pptx.author = 'DevCareer'
  pptx.title = `Career Report — ${report.github_username || 'Developer'}`
  pptx.subject = 'Developer Career Intelligence Report'

  const PURPLE = '7C3AED'
  const PINK = 'EC4899'
  const DARK = '111827'
  const GRAY = '6B7280'
  const WHITE = 'FFFFFF'
  const GREEN = '059669'

  // ─── Slide 1: Title ───
  const slide1 = pptx.addSlide()
  slide1.background = { color: DARK }
  slide1.addText('DevCareer', {
    x: 0.8, y: 1.0, w: 8.5, h: 1.0,
    fontSize: 42, fontFace: 'Arial', bold: true,
    color: PURPLE, align: 'center',
  })
  slide1.addText('Developer Career Intelligence Report', {
    x: 0.8, y: 2.0, w: 8.5, h: 0.6,
    fontSize: 20, fontFace: 'Arial', color: GRAY, align: 'center',
  })
  slide1.addText(`GitHub: @${report.github_username || 'unknown'}`, {
    x: 0.8, y: 3.0, w: 8.5, h: 0.5,
    fontSize: 16, fontFace: 'Arial', color: WHITE, align: 'center',
  })
  slide1.addText(`Generated: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`, {
    x: 0.8, y: 4.0, w: 8.5, h: 0.4,
    fontSize: 12, fontFace: 'Arial', color: GRAY, align: 'center',
  })

  // ─── Slide 2: Career Verdict ───
  const verdict = report.career_verdict
  if (verdict) {
    const slide2 = pptx.addSlide()
    slide2.background = { color: WHITE }
    slide2.addText('Career Verdict', {
      x: 0.5, y: 0.3, w: 9, h: 0.7,
      fontSize: 28, fontFace: 'Arial', bold: true, color: DARK,
    })

    const verdictColor = verdict.verdict === 'Senior' ? GREEN : verdict.verdict === 'Mid' ? 'D97706' : 'DC2626'
    slide2.addText(verdict.verdict || 'N/A', {
      x: 0.5, y: 1.2, w: 3, h: 1.0,
      fontSize: 36, fontFace: 'Arial', bold: true, color: verdictColor,
    })
    slide2.addText(`Confidence: ${Math.round((verdict.confidence || 0) * 100)}%`, {
      x: 3.5, y: 1.2, w: 3, h: 1.0,
      fontSize: 20, fontFace: 'Arial', color: GRAY,
    })

    // Evidence bullets
    if (verdict.verdict_evidence && verdict.verdict_evidence.length > 0) {
      slide2.addText('Key Evidence:', {
        x: 0.5, y: 2.5, w: 9, h: 0.4,
        fontSize: 14, fontFace: 'Arial', bold: true, color: DARK,
      })
      const evidenceText = verdict.verdict_evidence.slice(0, 4).map(e => `• ${e}`).join('\n')
      slide2.addText(evidenceText, {
        x: 0.5, y: 3.0, w: 9, h: 3.5,
        fontSize: 11, fontFace: 'Arial', color: GRAY, valign: 'top',
        lineSpacingMultiple: 1.3,
      })
    }
  }

  // ─── Slide 3: Repo Scores ───
  const repos = report.repo_scores || []
  if (repos.length > 0) {
    const slide3 = pptx.addSlide()
    slide3.background = { color: WHITE }
    slide3.addText('Repository Analysis', {
      x: 0.5, y: 0.3, w: 9, h: 0.7,
      fontSize: 28, fontFace: 'Arial', bold: true, color: DARK,
    })

    const rows = [
      [
        { text: 'Repository', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'Score', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'Issues', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
      ],
    ]
    repos.forEach(r => {
      const scoreColor = r.score >= 70 ? GREEN : r.score >= 50 ? 'D97706' : 'DC2626'
      rows.push([
        { text: r.repo_name || 'unknown', options: { color: DARK } },
        { text: `${r.score}/100`, options: { color: scoreColor, bold: true } },
        { text: `${(r.findings || []).length} findings`, options: { color: GRAY } },
      ])
    })

    slide3.addTable(rows, {
      x: 0.5, y: 1.3, w: 9, h: 0.4,
      fontSize: 12, fontFace: 'Arial',
      border: { type: 'solid', pt: 0.5, color: 'E5E7EB' },
      colW: [4, 2.5, 2.5],
      rowH: 0.45,
    })
  }

  // ─── Slide 4: 90-Day Roadmap ───
  const roadmap = verdict?.roadmap_90_days || []
  if (roadmap.length > 0) {
    const slide4 = pptx.addSlide()
    slide4.background = { color: WHITE }
    slide4.addText('90-Day Roadmap', {
      x: 0.5, y: 0.3, w: 9, h: 0.7,
      fontSize: 28, fontFace: 'Arial', bold: true, color: DARK,
    })

    const roadmapRows = [
      [
        { text: 'Weeks', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'Focus Area', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'Action', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'Hours', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
      ],
    ]
    roadmap.forEach(step => {
      roadmapRows.push([
        { text: `Week ${step.week}`, options: { color: PURPLE, bold: true } },
        { text: step.focus || '', options: { color: DARK } },
        { text: (step.action || '').slice(0, 80) + (step.action?.length > 80 ? '...' : ''), options: { color: GRAY, fontSize: 10 } },
        { text: `~${step.hours || 0}h`, options: { color: GRAY } },
      ])
    })

    slide4.addTable(roadmapRows, {
      x: 0.5, y: 1.2, w: 9,
      fontSize: 11, fontFace: 'Arial',
      border: { type: 'solid', pt: 0.5, color: 'E5E7EB' },
      colW: [1.2, 2.3, 4, 1.5],
      rowH: 0.5,
    })
  }

  // ─── Slide 5: Gap Analysis ───
  const gaps = verdict?.gap_analysis || []
  if (gaps.length > 0) {
    const slide5 = pptx.addSlide()
    slide5.background = { color: WHITE }
    slide5.addText('Gap Analysis — What\'s Blocking Your Next Level', {
      x: 0.5, y: 0.3, w: 9, h: 0.7,
      fontSize: 24, fontFace: 'Arial', bold: true, color: DARK,
    })

    const gapRows = [
      [
        { text: 'Gap', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'ROI', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
        { text: 'Fix', options: { bold: true, color: WHITE, fill: { color: PURPLE } } },
      ],
    ]
    gaps.forEach(g => {
      const roiColor = g.career_roi === 'high' ? GREEN : g.career_roi === 'medium' ? 'D97706' : GRAY
      gapRows.push([
        { text: g.gap || '', options: { color: DARK, bold: true } },
        { text: (g.career_roi || 'medium').toUpperCase(), options: { color: roiColor, bold: true } },
        { text: (g.fix || '').slice(0, 100) + (g.fix?.length > 100 ? '...' : ''), options: { color: GRAY, fontSize: 10 } },
      ])
    })

    slide5.addTable(gapRows, {
      x: 0.5, y: 1.2, w: 9,
      fontSize: 11, fontFace: 'Arial',
      border: { type: 'solid', pt: 0.5, color: 'E5E7EB' },
      colW: [3, 1.5, 4.5],
      rowH: 0.55,
    })
  }

  // ─── Slide 6: Resume Rewrite ───
  const bullets = verdict?.resume_bullets || []
  if (bullets.length > 0) {
    const slide6 = pptx.addSlide()
    slide6.background = { color: WHITE }
    slide6.addText('Resume Rewrite — Evidence-Based', {
      x: 0.5, y: 0.3, w: 9, h: 0.7,
      fontSize: 24, fontFace: 'Arial', bold: true, color: DARK,
    })

    let yPos = 1.2
    bullets.slice(0, 3).forEach(b => {
      slide6.addText(`${b.repo}`, {
        x: 0.5, y: yPos, w: 9, h: 0.3,
        fontSize: 13, fontFace: 'Arial', bold: true, color: PURPLE,
      })
      slide6.addText(`❌ "${b.original_claim}"`, {
        x: 0.7, y: yPos + 0.35, w: 8.5, h: 0.4,
        fontSize: 10, fontFace: 'Arial', color: 'DC2626', italic: true,
      })
      slide6.addText(`✓ "${b.rewritten}"`, {
        x: 0.7, y: yPos + 0.75, w: 8.5, h: 0.5,
        fontSize: 10, fontFace: 'Arial', color: GREEN,
      })
      yPos += 1.5
    })
  }

  // ─── Slide 7: Market Position ───
  const market = report.market_intel
  if (market) {
    const slide7 = pptx.addSlide()
    slide7.background = { color: WHITE }
    slide7.addText('Market Position', {
      x: 0.5, y: 0.3, w: 9, h: 0.7,
      fontSize: 28, fontFace: 'Arial', bold: true, color: DARK,
    })

    slide7.addText(`${market.percentile}th Percentile`, {
      x: 0.5, y: 1.2, w: 4, h: 1.0,
      fontSize: 36, fontFace: 'Arial', bold: true, color: PURPLE,
    })

    slide7.addText('Qualifying Roles:', {
      x: 0.5, y: 2.5, w: 9, h: 0.4,
      fontSize: 14, fontFace: 'Arial', bold: true, color: DARK,
    })
    const rolesText = (market.qualifying_roles || []).map(r => `• ${r}`).join('\n')
    slide7.addText(rolesText, {
      x: 0.7, y: 2.9, w: 8.5, h: 1.5,
      fontSize: 12, fontFace: 'Arial', color: GRAY, valign: 'top',
    })

    if (market.salary_unlock_skills?.length > 0) {
      slide7.addText('Skills to Unlock Next Salary Bracket:', {
        x: 0.5, y: 4.5, w: 9, h: 0.4,
        fontSize: 14, fontFace: 'Arial', bold: true, color: DARK,
      })
      slide7.addText(market.salary_unlock_skills.join('  •  '), {
        x: 0.7, y: 4.9, w: 8.5, h: 0.5,
        fontSize: 12, fontFace: 'Arial', color: PURPLE,
      })
    }
  }

  // Download
  await pptx.writeFile({ fileName: `${filename}.pptx` })
}
