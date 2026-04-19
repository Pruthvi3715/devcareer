const stages = [
  { id: 1, label: 'Fetching GitHub profile', icon: '👤' },
  { id: 2, label: 'Cloning and parsing repos', icon: '📦' },
  { id: 3, label: 'Running code analysis', icon: '🔍' },
  { id: 4, label: 'AI reviewing your code', icon: '🤖' },
  { id: 5, label: 'Generating career report', icon: '📊' },
]

export default function LoadingPipeline({ progress = 0, currentStage = 1 }) {
  const getStageStatus = (stageId) => {
    if (stageId < currentStage) return 'completed'
    if (stageId === currentStage) return 'active'
    return 'pending'
  }

  const getProgressForStage = (stageId) => {
    if (stageId > currentStage) return 0
    if (stageId < currentStage) return 100
    
    const stageProgress = 100 / stages.length
    const withinStageProgress = progress - (currentStage - 1) * stageProgress
    return Math.max(0, Math.min(100, withinStageProgress))
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8" role="status" aria-live="polite" aria-busy="true">
      <div className="max-w-xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2 text-white">Analyzing Your Code</h1>
          <p className="text-gray-400">This usually takes 30-90 seconds</p>
        </div>

        <div className="space-y-4">
          {stages.map((stage) => {
            const status = getStageStatus(stage.id)
            const stageProgress = getProgressForStage(stage.id)
            
            return (
              <div
                key={stage.id}
                className={`relative overflow-hidden rounded-lg border ${
                  status === 'active'
                    ? 'border-purple-500 bg-gray-900'
                    : status === 'completed'
                    ? 'border-green-600 bg-gray-900/50'
                    : 'border-gray-800 bg-gray-900/30'
                }`}
              >
                <div className="flex items-center p-4 relative z-10">
                  <div className={`text-2xl mr-4 ${
                    status === 'pending' ? 'opacity-30' : ''
                  }`}>
                    {status === 'completed' ? '✓' : stage.icon}
                  </div>
                  <div className="flex-1">
                    <p className={`font-medium ${
                      status === 'pending' ? 'text-gray-500' :
                      status === 'completed' ? 'text-green-400' :
                      'text-white'
                    }`}>
                      {stage.label}
                    </p>
                    {status === 'active' && (
                      <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                          style={{ width: `${stageProgress}%` }}
                        />
                      </div>
                    )}
                  </div>
                    {status === 'completed' && (
                    <span className="text-green-500 text-sm ml-4">Done</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-8 text-center text-gray-500">
          <p>Progress: {Math.round(progress)}%</p>
        </div>
      </div>
    </div>
  )
}