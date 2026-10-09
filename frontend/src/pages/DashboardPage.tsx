import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useSettings } from '../contexts/SettingsContext'
import type { ChildProfile } from '../types'

function displayAge(value?: string | null) {
  if (!value) return 'العمر غير مضاف'
  const birthDate = new Date(`${value}T00:00:00`)
  const today = new Date()
  let age = today.getFullYear() - birthDate.getFullYear()
  if (today.getMonth() < birthDate.getMonth() || (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate())) age--
  return age <= 0 ? 'أقل من سنة' : `${new Intl.NumberFormat('ar-SA').format(age)} سنوات`
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { t } = useSettings()
  const [children, setChildren] = useState<ChildProfile[]>([])
  const canAccessChildren = user?.role === 'guardian' || user?.role === 'care_provider'
  const [loading, setLoading] = useState(canAccessChildren)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!canAccessChildren) return
    setLoading(true)
    apiClient.get<ChildProfile[]>('/children')
      .then((response) => setChildren(response.data))
      .catch(() => setError('تعذر تحميل ملفات الأطفال.'))
      .finally(() => setLoading(false))
  }, [canAccessChildren])

  if (user?.role === 'center') return <Navigate to="/provider" replace />
  if (user?.role === 'admin') return <Navigate to="/admin" replace />

  if (!canAccessChildren) {
    return (
      <section className="provider-dashboard">
        <div className="soft-dashboard-banner">
          <div><span className="soft-kicker">مرحبًا {user?.full_name}</span><h1>مرحبًا بك في وئام</h1><p>يمكنك الوصول إلى الخدمات المتاحة لحسابك من هذه المساحة.</p></div>
          {user?.verification_status === 'unverified' && <span className="status-pill warning">غير موثّق</span>}
        </div>
      </section>
    )
  }

  if (loading) return <div className="loading-row"><div className="spinner" /> جاري تحميل الملفات...</div>

  if (user?.role === 'care_provider') {
    return (
      <section className="provider-dashboard">
        {error && <div className="alert alert-error">{error}</div>}
        <div className="soft-dashboard-banner">
          <div><span className="soft-kicker">مرحبًا {user.full_name}</span><h1>فريق الرعاية في مساحة واحدة</h1><p>تظهر هنا فقط ملفات الأطفال التي قُبلت دعوتك للوصول إليها وضمن الصلاحيات المحددة لك.</p></div>
          <div className="dashboard-banner-actions"><Link className="btn btn-outline" to="/invitations">عرض الدعوات</Link><Link className="btn btn-primary" to="/provider">مساحة مقدم الخدمة</Link></div>
        </div>
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
          <div className="prototype-empty-card"><span>✉</span><h2>لا توجد ملفات مصرح بها بعد</h2><p>افتحي صفحة الدعوات واقبلي دعوة ولي الأمر أولًا.</p><Link className="btn btn-primary" to="/invitations">عرض الدعوات</Link></div>
        )}
      </section>
    )
  }

  if (!children.length) {
    return (
      <section className="guardian-dashboard">
        <div className="m10-files-heading">
          <div><span className="soft-kicker">{t('dashboard.kicker')}</span><h1>ملفات الأطفال</h1><p>ابدئي من ملف الطفل للوصول إلى معلوماته وخدماته ومتابعاته في مكان واحد.</p></div>
          <Link className="btn btn-primary" to="/children/new">{t('dashboard.addChild')}</Link>
        </div>
        <div className="prototype-empty-card"><span>🌱</span><h2>لا يوجد ملف طفل بعد</h2><p>سنطلب فقط المعلومات الأساسية الآن، ويمكن إكمال الباقي تدريجيًا.</p><Link className="btn btn-primary" to="/children/new">إنشاء ملف طفل</Link></div>
      </section>
    )
  }

  return (
    <section className="guardian-dashboard m10-children-dashboard">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="m10-files-heading">
        <div><span className="soft-kicker">الرئيسية</span><h1>ملفات الأطفال</h1><p>اختاري ملف الطفل الذي تريدين متابعته. لكل طفل مساحة مستقلة تجمع النظرة العامة والخدمات والتحديثات.</p></div>
        <Link className="btn btn-primary" to="/children/new">＋ إضافة ملف طفل</Link>
      </div>

      <div className="m10-child-file-grid" aria-label="ملفات الأطفال">
        {children.map((child) => {
          const displayName = child.preferred_name || child.first_name
          return (
            <Link key={child.id} to={`/children/${child.id}`} className="m10-child-file-card" aria-label={`فتح ملف ${displayName}`}>
              <span className="m10-child-file-avatar">{child.first_name.slice(0, 1)}</span>
              <div className="m10-child-file-copy">
                <span className="m10-child-file-label">ملف الطفل</span>
                <h2>{displayName}</h2>
                <div className="m10-child-file-meta">
                  <span>{displayAge(child.birth_date)}</span>
                  <span>{child.services.length ? `${new Intl.NumberFormat('ar-SA').format(child.services.length)} خدمات حالية` : 'لا توجد خدمات مضافة'}</span>
                  <span>آخر تحديث {new Date(child.updated_at).toLocaleDateString('ar-SA-u-ca-gregory')}</span>
                </div>
              </div>
              <span className="m10-child-file-chevron" aria-hidden="true">←</span>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
