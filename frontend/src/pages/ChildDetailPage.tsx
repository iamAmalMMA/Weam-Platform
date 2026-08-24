import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiClient } from '../api/client'
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

function ProfileSection({ title, description, items, tone }: { title: string; description: string; items: string[]; tone: string }) {
  return (
    <div className={`m9-profile-data-row ${tone}`}>
      <div><strong>{title}</strong><small>{description}</small></div>
      <Tags items={items} />
    </div>
  )
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

  const featureLinks = [
    { label: 'التقارير', shortLabel: 'التقارير', to: `/children/${child.id}/reports`, allowed: canViewReports, icon: '▤' },
    { label: 'الأهداف', shortLabel: 'الأهداف', to: `/children/${child.id}/goals`, allowed: canViewGoals, icon: '◎' },
    { label: 'المتابعات', shortLabel: 'المتابعات', to: `/children/${child.id}/follow-ups`, allowed: canViewTimeline, icon: '✓' },
    { label: 'الملاحظات الصوتية', shortLabel: 'الملاحظات الصوتية', to: `/children/${child.id}/voice-notes`, allowed: canViewVoice, icon: '◉' },
    { label: 'الخط الزمني', shortLabel: 'الخط الزمني', to: `/children/${child.id}/timeline`, allowed: canViewTimeline, icon: '↻' },
    { label: 'فريق الرعاية', shortLabel: 'فريق الرعاية', to: `/children/${child.id}/care-team`, allowed: canViewCareTeam, icon: '♧' },
    { label: 'التواصل', shortLabel: 'التواصل', to: `/children/${child.id}/communication`, allowed: canMessageTeam, icon: '◇' },
    { label: 'مساعد وئام', shortLabel: 'مساعد وئام', to: `/children/${child.id}/assistant`, allowed: true, icon: '✦' },
    { label: 'مراكز مناسبة', shortLabel: 'المراكز', to: `/children/${child.id}/center-matches`, allowed: true, icon: '⌖' },
  ]

  const cancelEditing = () => {
    setDraft(draftFromChild(child))
    setSaveError('')
    setSaved(false)
    setEditing(false)
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
    <section className="prototype-detail-page m9-child-profile-page">
      <header className="m9-child-page-heading">
        <div><span className="soft-kicker">مساحة ولي الأمر</span><h1>ملف {displayName}</h1><p>صورة واضحة ومختصرة للاحتياجات والخدمات وخطوات الرعاية.</p></div>
        <div className="m9-child-heading-actions">
          {canViewCareTeam && <Link className="btn btn-outline" to={`/children/${child.id}/care-team`}>فريق الرعاية</Link>}
          {canViewReports && <Link className="btn btn-primary" to={`/children/${child.id}/reports`}>إضافة تقرير</Link>}
        </div>
      </header>

      {saved && <div className="alert m9-save-success">تم تحديث معلومات الطفل بنجاح.</div>}

      <div className="m9-child-profile-hero">
        <div className="m9-child-profile-identity">
          <div className="m9-child-profile-avatar"><span>{child.first_name.slice(0, 1)}</span></div>
          <div className="m9-child-profile-copy">
            <span className="status-pill success">ملف رعاية نشط</span>
            <h2>{displayName}</h2>
            <p>{displayAge(child.birth_date)} · {displayGender(child.gender)} · آخر تحديث {new Date(child.updated_at).toLocaleDateString('ar-SA-u-ca-gregory')}</p>
            <div className="m9-child-highlights">
              {highlights.length ? highlights.map((item) => <span key={item}>{item}</span>) : <span className="needs-completion">الملف يحتاج استكمال المعلومات</span>}
            </div>
          </div>
        </div>
        <div className="m9-profile-status" aria-label="حالة ملف الرعاية">
          <span aria-hidden="true">✓</span>
          <div><strong>ملف الرعاية</strong><small>{allCareFieldsEmpty ? 'بانتظار استكمال المعلومات' : 'المعلومات متاحة للفريق'}</small></div>
        </div>
      </div>

      <nav className="m9-child-feature-tabs" aria-label="أقسام ملف الطفل">
        <Link className="active" to={`/children/${child.id}`}><span>⌂</span>نظرة عامة</Link>
        {featureLinks.map((item) => item.allowed
          ? <Link key={item.to} to={item.to}><span>{item.icon}</span>{item.shortLabel}</Link>
          : <span key={item.to} className="disabled" title={`${item.label} غير مصرح`}><i>{item.icon}</i>{item.shortLabel}</span>)}
      </nav>

      {editing && primary && (
        <form className="m9-child-edit-panel" onSubmit={saveProfile}>
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

      <div className="m9-child-overview-grid">
        <article className="m9-care-profile-card">
          <div className="m9-overview-card-heading">
            <div><span className="soft-kicker">نبذة الملف</span><h2>الاحتياجات والرعاية الحالية</h2><p>معلومات عملية يستخدمها الفريق لفهم حالة الطفل وطريقة دعمه.</p></div>
            {primary && <button type="button" className="m9-edit-profile-button" aria-expanded={editing} onClick={() => { setEditing((value) => !value); setSaved(false) }}>{editing ? 'إغلاق التعديل' : 'تحديث المعلومات'}</button>}
          </div>
          {allCareFieldsEmpty && <div className="m9-care-empty-callout"><strong>لم تكتمل معلومات الرعاية بعد</strong><span>أضيفي الحالة والاحتياجات والخدمات حتى تصبح المطابقة وإجابات المساعد أكثر دقة.</span>{primary && !editing && <button type="button" onClick={() => setEditing(true)}>استكمال المعلومات</button>}</div>}
          <div className="m9-profile-data-list">
            <ProfileSection title="الحالة" description="التشخيص أو الحالة المعروفة" items={child.conditions} tone="mint" />
            <ProfileSection title="الاحتياجات" description="المهارات والجوانب التي تحتاج دعمًا" items={child.needs} tone="pink" />
            <ProfileSection title="متطلبات الدعم" description="الأسلوب أو البيئة المناسبة للطفل" items={child.support_requirements} tone="gold" />
            <ProfileSection title="الخدمات الحالية" description="الخدمات التي يتلقاها الطفل الآن" items={child.services} tone="violet" />
          </div>
        </article>

        <aside className="m9-child-info-card">
          <div><span className="soft-kicker">معلومات الملف</span><h2>بيانات أساسية</h2></div>
          <dl>
            <div><dt>تاريخ الميلاد</dt><dd>{child.birth_date ? new Date(`${child.birth_date}T00:00:00`).toLocaleDateString('ar-SA-u-ca-gregory') : 'غير مضاف'}</dd></div>
            <div><dt>الجنس</dt><dd>{displayGender(child.gender)}</dd></div>
            <div><dt>صفة الوصول</dt><dd>{accessLabel}</dd></div>
            <div><dt>الخدمات الحالية</dt><dd>{child.services.length ? `${new Intl.NumberFormat('ar-SA').format(child.services.length)} خدمات` : 'لا توجد خدمات مضافة'}</dd></div>
          </dl>
          {child.summary && <div className="m9-child-summary"><strong>نبذة عن الطفل</strong><p>{child.summary}</p></div>}
        </aside>
      </div>

      <div className="prototype-next-banner m9-child-next-step"><div><span className="soft-kicker">المتابعات</span><h2>المواعيد المهمة تبقى قريبة منك</h2><p>تظهر المتابعات في ملف الطفل والخط الزمني، ويذكّرك وئام بها عند اقتراب موعدها.</p></div>{canViewTimeline ? <Link className="btn btn-white" to={`/children/${child.id}/follow-ups`}>عرض المتابعات</Link> : <span>🔔</span>}</div>
    </section>
  )
}
