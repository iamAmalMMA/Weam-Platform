import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import ChildProgressCharts from '../components/ChildProgressCharts'
import TagEditor from '../components/TagEditor'
import type { ChildProfile } from '../types'

type ChildDraft = {
  first_name: string
  preferred_name: string
  birth_date: string
  gender: string
  summary: string
  conditions: string[]
  needs: string[]
  support_requirements: string[]
  services: string[]
}

type FeatureTone = 'blue' | 'violet' | 'teal' | 'rose' | 'gold'

type FeatureLink = {
  label: string
  description: string
  to: string
  allowed: boolean
  icon: string
  tone: FeatureTone
}

const emptyDraft: ChildDraft = {
  first_name: '', preferred_name: '', birth_date: '', gender: '', summary: '',
  conditions: [], needs: [], support_requirements: [], services: [],
}

function draftFromChild(child: ChildProfile): ChildDraft {
  return {
    first_name: child.first_name,
    preferred_name: child.preferred_name || '',
    birth_date: child.birth_date || '',
    gender: child.gender || '',
    summary: child.summary || '',
    conditions: [...child.conditions],
    needs: [...child.needs],
    support_requirements: [...child.support_requirements],
    services: [...child.services],
  }
}

function displayGender(value?: string | null) {
  if (value === 'female') return 'أنثى'
  if (value === 'male') return 'ذكر'
  if (value === 'other') return 'غير محدد'
  return 'غير مضاف'
}

function displayAge(value?: string | null) {
  if (!value) return 'العمر غير مضاف'
  const birthDate = new Date(`${value}T00:00:00`)
  const today = new Date()
  let age = today.getFullYear() - birthDate.getFullYear()
  if (today.getMonth() < birthDate.getMonth() || (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate())) age--
  return age <= 0 ? 'أقل من سنة' : `${new Intl.NumberFormat('ar-SA').format(age)} سنوات`
}

function Tags({ items, empty = 'غير مضافة' }: { items: string[]; empty?: string }) {
  if (!items.length) return <span className="m9-profile-empty-value">{empty}</span>
  return <div className="detail-tags">{items.map((item) => <span key={item}>{item}</span>)}</div>
}

export default function ChildDetailPage() {
  const { childId } = useParams()
  const [child, setChild] = useState<ChildProfile | null>(null)
  const [draft, setDraft] = useState<ChildDraft>(emptyDraft)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saved, setSaved] = useState(false)
  const [infoOpen, setInfoOpen] = useState(false)
  const editPanelRef = useRef<HTMLFormElement | null>(null)

  useEffect(() => {
    apiClient.get<ChildProfile>(`/children/${childId}`)
      .then((response) => {
        setChild(response.data)
        setDraft(draftFromChild(response.data))
      })
      .catch(() => setError('لم نتمكن من فتح هذا الملف، أو لا تملكين صلاحية الوصول إليه.'))
  }, [childId])

  if (error) return <div className="prototype-empty-card"><h2>تعذر فتح الملف</h2><p>{error}</p><Link className="btn btn-primary" to="/dashboard">العودة للرئيسية</Link></div>
  if (!child) return <div className="loading-row"><div className="spinner" /> جاري تحميل الملف...</div>

  const accessLabel = child.access_role === 'care_provider'
    ? 'مقدم رعاية'
    : child.guardian_type === 'primary' ? 'ولي أمر رئيسي' : 'ولي أمر ثانوي'
  const primary = child.guardian_type === 'primary'
  const canViewReports = primary || child.access_permissions.includes('view_reports')
  const canViewCareTeam = primary || child.access_permissions.includes('view_care_team')
  const canViewGoals = primary || child.access_permissions.includes('view_goals')
  const canViewTimeline = primary || child.access_permissions.includes('view_timeline')
  const canViewVoice = primary || child.access_permissions.includes('view_voice_notes')
  const canMessageTeam = primary || child.access_permissions.includes('message_team')
  const displayName = child.preferred_name || child.first_name
  const highlights = Array.from(new Set([...child.needs, ...child.conditions, ...child.services])).slice(0, 3)
  const allCareFieldsEmpty = !child.conditions.length && !child.needs.length && !child.support_requirements.length && !child.services.length

  const featureLinks: FeatureLink[] = [
    { label: 'التقارير', description: 'تقارير الطفل وتحليلها', to: `/children/${child.id}/reports`, allowed: canViewReports, icon: '▤', tone: 'blue' },
    { label: 'الأهداف', description: 'خطط وأهداف التقدم', to: `/children/${child.id}/goals`, allowed: canViewGoals, icon: '◎', tone: 'violet' },
    { label: 'المتابعات', description: 'المهام والمواعيد القادمة', to: `/children/${child.id}/follow-ups`, allowed: canViewTimeline, icon: '✓', tone: 'teal' },
    { label: 'الملاحظات الصوتية', description: 'تسجيل وتحويل إلى نص', to: `/children/${child.id}/voice-notes`, allowed: canViewVoice, icon: '◉', tone: 'rose' },
    { label: 'فريق الرعاية', description: 'الأعضاء والأدوار والصلاحيات', to: `/children/${child.id}/care-team`, allowed: canViewCareTeam, icon: '♧', tone: 'violet' },
    { label: 'الرسائل', description: 'تواصل آمن مع الفريق', to: `/children/${child.id}/communication`, allowed: canMessageTeam, icon: '◇', tone: 'blue' },
    { label: 'مساعد وئام', description: 'أسئلة من بيانات الطفل', to: `/children/${child.id}/assistant`, allowed: true, icon: '✦', tone: 'gold' },
    { label: 'الخط الزمني', description: 'سجل موحد لأهم التحديثات', to: `/children/${child.id}/timeline`, allowed: canViewTimeline, icon: '↻', tone: 'teal' },
    { label: 'مراكز مناسبة', description: 'مراكز وخدمات تناسب احتياجات الطفل', to: `/children/${child.id}/center-matches`, allowed: true, icon: '⌖', tone: 'rose' },
  ]

  const cancelEditing = () => {
    setDraft(draftFromChild(child))
    setSaveError('')
    setSaved(false)
    setEditing(false)
  }

  const startEditing = () => {
    setInfoOpen(false)
    setSaved(false)
    setEditing(true)
    window.setTimeout(() => {
      const panel = editPanelRef.current
      if (!panel) return
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' })
      const firstField = panel.querySelector<HTMLElement>('input, textarea, select')
      firstField?.focus({ preventScroll: true })
    }, 80)
  }

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setSaveError('')
    setSaved(false)
    try {
      const response = await apiClient.patch<ChildProfile>(`/children/${child.id}`, {
        first_name: draft.first_name.trim(),
        preferred_name: draft.preferred_name.trim() || null,
        birth_date: draft.birth_date || null,
        gender: draft.gender || null,
        summary: draft.summary.trim() || null,
        conditions: draft.conditions,
        needs: draft.needs,
        support_requirements: draft.support_requirements,
        services: draft.services,
      })
      setChild(response.data)
      setDraft(draftFromChild(response.data))
      setEditing(false)
      setSaved(true)
    } catch {
      setSaveError('تعذر حفظ معلومات الطفل. تحققي من البيانات وحاولي مرة أخرى.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="prototype-detail-page m9-child-profile-page m10-child-profile-page">
      <header className="m9-child-page-heading m10-child-page-heading">
        <div><span className="soft-kicker">ملف الطفل</span><h1>ملف {displayName}</h1><p>نظرة سريعة على الطفل، ثم وصول مباشر إلى خدمات ملفه.</p></div>
        <div className="m9-child-heading-actions">
          <button type="button" className="btn btn-outline" onClick={() => setInfoOpen(true)}>معلومات الطفل</button>
          {canViewCareTeam && <Link className="btn btn-outline" to={`/children/${child.id}/care-team`}>فريق الرعاية</Link>}
          {canViewReports && <Link className="btn btn-primary" to={`/children/${child.id}/reports`}>إضافة تقرير</Link>}
        </div>
      </header>

      {saved && <div className="alert m9-save-success">تم تحديث معلومات الطفل بنجاح.</div>}

      <div className="m9-child-profile-hero m10-child-profile-hero">
        <div className="m9-child-profile-identity">
          <div className="m9-child-profile-avatar"><span>{child.first_name.slice(0, 1)}</span></div>
          <div className="m9-child-profile-copy">
            <h2>{displayName}</h2>
            <p>{displayAge(child.birth_date)} · {displayGender(child.gender)} · آخر تحديث {new Date(child.updated_at).toLocaleDateString('ar-SA-u-ca-gregory')}</p>
            <div className="m9-child-highlights">
              {highlights.length ? highlights.map((item) => <span key={item}>{item}</span>) : <span className="needs-completion">الملف يحتاج استكمال المعلومات</span>}
            </div>
          </div>
        </div>
        <button type="button" className="m10-profile-info-button" onClick={() => setInfoOpen(true)}>
          <span aria-hidden="true">i</span>
          <div><strong>معلومات الطفل</strong><small>البيانات الأساسية والنبذة</small></div>
        </button>
      </div>

      <ChildProgressCharts childId={child.id} canViewGoals={canViewGoals} canViewFollowUps={canViewTimeline} />

      <section className="m10-child-services-section" aria-labelledby="child-services-title">
        <div className="m10-section-heading">
          <div><span className="soft-kicker">الوصول السريع</span><h2 id="child-services-title">خدمات ملف الطفل</h2><p>اختاري الخدمة المطلوبة للوصول مباشرة إلى تفاصيلها.</p></div>
        </div>
        <div className="m10-child-services-grid">
          {featureLinks.map((item) => item.allowed ? (
            <Link key={item.to} to={item.to} className={`m10-service-card ${item.tone}`}>
              <span className="m10-service-icon" aria-hidden="true">{item.icon}</span>
              <div><strong>{item.label}</strong><small>{item.description}</small></div>
            </Link>
          ) : (
            <div key={item.to} className={`m10-service-card disabled ${item.tone}`} title={`${item.label} غير مصرح`}>
              <span className="m10-service-icon" aria-hidden="true">{item.icon}</span>
              <div><strong>{item.label}</strong><small>غير متاح حسب الصلاحية</small></div>
            </div>
          ))}
        </div>
      </section>

      {editing && primary && (
        <form ref={editPanelRef} className="m9-child-edit-panel" onSubmit={saveProfile}>
          <div className="m9-child-edit-heading"><div><span className="soft-kicker">تحديث الملف</span><h2>معلومات الطفل واحتياجاته</h2><p>هذه المعلومات تساعد فريق الرعاية ومساعد وئام ومطابقة المراكز.</p></div><button type="button" className="btn btn-white btn-small" onClick={cancelEditing}>إلغاء</button></div>
          {saveError && <div className="alert alert-error">{saveError}</div>}
          <div className="form-grid two">
            <label>الاسم الأول<input required value={draft.first_name} onChange={(event) => setDraft({ ...draft, first_name: event.target.value })} /></label>
            <label>الاسم المفضل<input value={draft.preferred_name} onChange={(event) => setDraft({ ...draft, preferred_name: event.target.value })} /></label>
            <label>تاريخ الميلاد<input type="date" max={new Date().toISOString().slice(0, 10)} value={draft.birth_date} onChange={(event) => setDraft({ ...draft, birth_date: event.target.value })} /></label>
            <label>الجنس<select value={draft.gender} onChange={(event) => setDraft({ ...draft, gender: event.target.value })}><option value="">غير محدد</option><option value="female">أنثى</option><option value="male">ذكر</option><option value="other">غير محدد</option></select></label>
          </div>
          <label className="m9-child-summary-field">نبذة مختصرة<textarea rows={3} value={draft.summary} onChange={(event) => setDraft({ ...draft, summary: event.target.value })} placeholder="ملخص يساعد فريق الرعاية على فهم الطفل بسرعة" /></label>
          <div className="m9-child-tags-editor-grid">
            <TagEditor label="الحالة أو الحالات" value={draft.conditions} onChange={(conditions) => setDraft({ ...draft, conditions })} placeholder="مثال: ضعف سمع" />
            <TagEditor label="الاحتياجات" value={draft.needs} onChange={(needs) => setDraft({ ...draft, needs })} placeholder="مثال: دعم التواصل" />
            <TagEditor label="متطلبات الدعم" value={draft.support_requirements} onChange={(support_requirements) => setDraft({ ...draft, support_requirements })} placeholder="مثال: تعليمات مرئية" />
            <TagEditor label="الخدمات الحالية" value={draft.services} onChange={(services) => setDraft({ ...draft, services })} placeholder="مثال: تخاطب" />
          </div>
          <div className="m9-child-edit-actions"><button className="btn btn-primary" disabled={saving}>{saving ? 'جاري الحفظ...' : 'حفظ معلومات الطفل'}</button></div>
        </form>
      )}

      <article className="m9-care-profile-card m10-care-summary-card">
        <div className="m9-overview-card-heading m10-care-heading">
          <div><h2>الاحتياجات والرعاية الحالية</h2><p>ملخص سريع لفهم ما يحتاجه الطفل وطريقة دعمه والخدمات التي يتلقاها الآن.</p></div>
          {primary && <button type="button" className="m9-edit-profile-button" aria-expanded={editing} onClick={() => { if (editing) cancelEditing(); else startEditing() }}>{editing ? 'إغلاق التعديل' : 'تحديث المعلومات'}</button>}
        </div>

        {allCareFieldsEmpty ? (
          <div className="m9-care-empty-callout"><strong>لم تكتمل معلومات الرعاية بعد</strong><span>أضيفي الحالة والاحتياجات والخدمات حتى تصبح المطابقة وإجابات المساعد أكثر دقة.</span>{primary && !editing && <button type="button" onClick={startEditing}>استكمال المعلومات</button>}</div>
        ) : (
          <div className="m10-care-overview-grid">
            <div className="m10-care-overview-item mint">
              <div className="m10-care-overview-title"><span aria-hidden="true" /><div><strong>الحالة</strong><small>التشخيص أو الحالة المعروفة</small></div></div>
              <Tags items={child.conditions} />
            </div>
            <div className="m10-care-overview-item pink">
              <div className="m10-care-overview-title"><span aria-hidden="true" /><div><strong>الاحتياجات</strong><small>المهارات والجوانب التي تحتاج دعمًا</small></div></div>
              <Tags items={child.needs} />
            </div>
            <div className="m10-care-overview-item gold">
              <div className="m10-care-overview-title"><span aria-hidden="true" /><div><strong>متطلبات الدعم</strong><small>الأسلوب أو البيئة المناسبة للطفل</small></div></div>
              <Tags items={child.support_requirements} />
            </div>
            <div className="m10-care-overview-item violet">
              <div className="m10-care-overview-title"><span aria-hidden="true" /><div><strong>الخدمات الحالية</strong><small>الخدمات التي يتلقاها الطفل الآن</small></div></div>
              <Tags items={child.services} />
            </div>
          </div>
        )}
      </article>

      <div className="prototype-next-banner m9-child-next-step"><div><span className="soft-kicker">المتابعات</span><h2>المواعيد المهمة تبقى قريبة منك</h2><p>تظهر المتابعات في ملف الطفل والخط الزمني، ويذكّرك وئام بها عند اقتراب موعدها.</p></div>{canViewTimeline ? <Link className="btn btn-white" to={`/children/${child.id}/follow-ups`}>عرض المتابعات</Link> : <span>🔔</span>}</div>

      {infoOpen && (
        <div className="m10-info-modal" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setInfoOpen(false) }}>
          <section className="m10-info-modal-card" role="dialog" aria-modal="true" aria-labelledby="child-info-title">
            <div className="m10-info-modal-head">
              <div><span className="soft-kicker">معلومات الملف</span><h2 id="child-info-title">معلومات {displayName}</h2></div>
              <button type="button" aria-label="إغلاق" onClick={() => setInfoOpen(false)}>×</button>
            </div>
            <dl className="m10-info-list">
              <div><dt>تاريخ الميلاد</dt><dd>{child.birth_date ? new Date(`${child.birth_date}T00:00:00`).toLocaleDateString('ar-SA-u-ca-gregory') : 'غير مضاف'}</dd></div>
              <div><dt>الجنس</dt><dd>{displayGender(child.gender)}</dd></div>
              <div><dt>صفة الوصول</dt><dd>{accessLabel}</dd></div>
              <div><dt>الخدمات الحالية</dt><dd>{child.services.length ? `${new Intl.NumberFormat('ar-SA').format(child.services.length)} خدمات` : 'لا توجد خدمات مضافة'}</dd></div>
            </dl>
            {child.summary && <div className="m9-child-summary"><strong>نبذة عن الطفل</strong><p>{child.summary}</p></div>}
            {primary && <div className="m10-info-modal-actions"><button type="button" className="btn btn-primary" onClick={startEditing}>تحديث معلومات الطفل</button></div>}
          </section>
        </div>
      )}
    </section>
  )
}
