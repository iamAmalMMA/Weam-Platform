import { useEffect, useState } from 'react'
import { apiClient } from '../api/client'
import type { ChildGoal, FollowUpItem } from '../types'

interface Props {
  childId: string
  canViewGoals: boolean
  canViewFollowUps: boolean
}

function weekBuckets(count: number, now: Date) {
  const buckets: { start: Date; end: Date }[] = []
  for (let i = count - 1; i >= 0; i--) {
    const end = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000)
    const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000)
    buckets.push({ start, end })
  }
  return buckets
}

export default function ChildProgressCharts({ childId, canViewGoals, canViewFollowUps }: Props) {
  const [goals, setGoals] = useState<ChildGoal[] | null>(null)
  const [followUps, setFollowUps] = useState<FollowUpItem[] | null>(null)

  useEffect(() => {
    if (!canViewGoals) return
    apiClient.get<ChildGoal[]>(`/children/${childId}/goals`)
      .then((response) => setGoals(response.data))
      .catch(() => setGoals([]))
  }, [childId, canViewGoals])

  useEffect(() => {
    if (!canViewFollowUps) return
    apiClient.get<FollowUpItem[]>(`/children/${childId}/follow-ups`, { params: { status: 'all' } })
      .then((response) => setFollowUps(response.data))
      .catch(() => setFollowUps([]))
  }, [childId, canViewFollowUps])

  if (!canViewGoals && !canViewFollowUps) return null

  const activeGoals = (goals || [])
    .filter((goal) => goal.status !== 'completed')
    .sort((a, b) => b.progress_percent - a.progress_percent)
    .slice(0, 5)

  const openCount = (followUps || []).filter((item) => item.status === 'open').length
  const dueSoonCount = (followUps || []).filter((item) => item.display_status === 'today' || item.display_status === 'overdue').length
  const completedItems = (followUps || []).filter((item) => item.status === 'completed' && item.completed_at)

  const now = new Date()
  const buckets = weekBuckets(8, now)
  let running = 0
  const points = buckets.map((bucket, index) => {
    running += completedItems.filter((item) => {
      const at = new Date(item.completed_at as string)
      return at > bucket.start && at <= bucket.end
    }).length
    return { x: index, y: running }
  })
  const maxY = Math.max(1, ...points.map((point) => point.y))
  const chartW = 320
  const chartH = 90
  const toX = (i: number) => (i / (points.length - 1)) * chartW
  const toY = (y: number) => chartH - (y / maxY) * (chartH - 12) - 4
  const path = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${toX(index).toFixed(1)} ${toY(point.y).toFixed(1)}`).join(' ')
  const hasTrend = completedItems.length >= 2

  const showGoals = canViewGoals && goals !== null
  const showFollowUps = canViewFollowUps && followUps !== null
  if (!showGoals && !showFollowUps) return null

  return (
    <article className="m9-progress-card">
      <div className="m9-overview-card-heading">
        <div><span className="soft-kicker">نظرة سريعة</span><h2>التقدم والمتابعات</h2><p>ملخص مرئي لتقدم الأهداف وحالة المتابعات في مكان واحد.</p></div>
      </div>

      <div className="m9-progress-grid">
        {showGoals && (
          <div className="m9-progress-goals">
            <h3>تقدم الأهداف النشطة</h3>
            {activeGoals.length === 0 ? (
              <p className="m9-profile-empty-value">لا توجد أهداف نشطة حاليًا.</p>
            ) : (
              <ul className="m9-goal-bars" aria-label="نسبة تقدم كل هدف">
                {activeGoals.map((goal) => (
                  <li key={goal.id}>
                    <div className="m9-goal-bar-label">
                      <span>{goal.title}</span>
                      <b>{goal.progress_percent}%</b>
                    </div>
                    <div className="m9-goal-bar-track" role="img" aria-label={`${goal.title}: ${goal.progress_percent}٪`}>
                      <div className="m9-goal-bar-fill" style={{ width: `${goal.progress_percent}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {showFollowUps && (
          <div className="m9-progress-followups">
            <h3>حالة المتابعات</h3>
            <div className="m9-followup-stats">
              <div><b>{openCount}</b><span>مفتوحة</span></div>
              <div className={dueSoonCount ? 'warn' : ''}><b>{dueSoonCount}</b><span>قريبة أو اليوم</span></div>
              <div><b>{completedItems.length}</b><span>مكتملة</span></div>
            </div>
            {hasTrend ? (
              <>
                <svg className="m9-followup-line" viewBox={`0 0 ${chartW} ${chartH}`} role="img" aria-label="عدد المتابعات المكتملة تراكميًا خلال آخر 8 أسابيع">
                  <path d={path} fill="none" stroke="#4338CA" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  {points.map((point, index) => (
                    <circle key={index} cx={toX(index)} cy={toY(point.y)} r="2.6" fill="#4338CA" />
                  ))}
                </svg>
                <small className="m9-followup-line-caption">إجمالي المتابعات المكتملة تراكميًا، آخر 8 أسابيع</small>
              </>
            ) : (
              <p className="m9-profile-empty-value">سيظهر الرسم البياني بعد إكمال متابعتين على الأقل.</p>
            )}
          </div>
        )}
      </div>
    </article>
  )
}
