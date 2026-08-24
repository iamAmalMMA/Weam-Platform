import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { ChildProfile, ProviderDashboard } from '../types'
import '../styles/provider-portal.css'

const verificationLabels = {
  verified: 'موثّق',
  unverified: 'قيد المراجعة',
  rejected: 'يحتاج تعديل',
}

export default function ProviderDashboardPage() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState<ProviderDashboard | null>(null)
  const [children, setChildren] = useState<ChildProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      apiClient.get<ProviderDashboard>('/provider/dashboard'),
      apiClient.get<ChildProfile[]>('/children'),
    ])
      .then(([dashboardResponse, childrenResponse]) => {
        setDashboard(dashboardResponse.data)
        setChildren(childrenResponse.data)
      })
      .catch(() => setError('تعذر تحميل مساحة مقدم الخدمة.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-row"><div className="spinner" /> جاري تجهيز مساحة مقدم الخدمة...</div>

  return (
    <section className="provider-portal-page">
      <div className="provider-portal-hero">
        <div><span className="soft-kicker">مساحة مقدم الخدمة</span><h1>مرحبًا {user?.full_name}</h1><p>إدارة واضحة لبيانات الجهة والملفات التي منحك أصحابها صلاحية الوصول إليها.</p></div>
        <Link className="btn btn-white" to="/invitations">عرض الدعوات</Link>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {user?.role === 'center' && (
        !dashboard?.center ? (
          <div className="provider-setup-card"><span>⌂</span><div><h2>استكمال ملف المركز</h2><p>إضافة الخدمات والتخصصات ومعلومات التواصل، ثم إرسال الملف للمراجعة.</p></div><Link className="btn btn-primary" to="/provider/center">إنشاء ملف المركز</Link></div>
        ) : (
          <div className="provider-center-overview">
            <div><span className={`status-pill ${dashboard.center.verification_status === 'verified' ? 'success' : 'warning'}`}>{verificationLabels[dashboard.center.verification_status]}</span><h2>{dashboard.center.name}</h2><p>{dashboard.center.city} · {dashboard.center.services.slice(0, 3).join('، ') || 'لم تُضف خدمات بعد'}</p></div>
            <div className="provider-overview-stats"><article><strong>{dashboard.specialists_count}</strong><span>مختصون</span></article><article><strong>{dashboard.authorized_children_count}</strong><span>ملفات مصرح بها</span></article></div>
            <Link className="btn btn-outline" to="/provider/center">إدارة ملف المركز</Link>
          </div>
        )
      )}

      <div className="provider-section-heading"><div><span className="soft-kicker">الوصول المصرح</span><h2>ملفات الأطفال</h2></div><small>لا تظهر هنا إلا الملفات المرتبطة بدعوة مقبولة وصلاحية فعالة.</small></div>
      {children.length ? (
        <div className="provider-child-grid">
          {children.map((child) => (
            <Link key={child.id} to={`/children/${child.id}`} className="provider-child-card">
              <span className="provider-child-avatar">{child.first_name.slice(0, 1)}</span>
              <div><small>ملف مصرح</small><h2>{child.preferred_name || child.first_name}</h2><p>{child.needs[0] || child.services[0] || 'ملف رعاية'}</p></div>
              <span>←</span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="prototype-empty-card"><span>✉</span><h2>لا توجد ملفات مصرح بها</h2><p>يبدأ الوصول بعد قبول دعوة ولي الأمر، ولا يمنح حساب المركز وصولًا عامًا إلى ملفات الأطفال.</p><Link className="btn btn-primary" to="/invitations">عرض الدعوات</Link></div>
      )}
    </section>
  )
}
