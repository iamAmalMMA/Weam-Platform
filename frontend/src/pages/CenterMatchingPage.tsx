import { useEffect, useState } from 'react'
import { isAxiosError } from 'axios'
import { Link, useParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import type {
  CenterFilterOptions,
  CenterMatchDeliveryMode,
  CenterMatchResult,
  ChildProfile,
} from '../types'
import '../styles/center-matching.css'

const levelLabels = {
  strong: 'توافق قوي',
  good: 'توافق جيد',
  initial: 'توافق مبدئي',
}

const matchingCountLabel = (count: number) => {
  if (count === 1) return 'خيار واحد مناسب بناءً على احتياجات الملف'
  if (count === 2) return 'خياران مناسبان بناءً على احتياجات الملف'
  return `${count} خيارات مناسبة بناءً على احتياجات الملف`
}

export default function CenterMatchingPage() {
  const { childId } = useParams()
  const [child, setChild] = useState<ChildProfile | null>(null)
  const [cities, setCities] = useState<string[]>([])
  const [city, setCity] = useState('')
  const [deliveryMode, setDeliveryMode] = useState<CenterMatchDeliveryMode | ''>('')
  const [result, setResult] = useState<CenterMatchResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [matching, setMatching] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    setLoading(true)
    Promise.all([
      apiClient.get<ChildProfile>(`/children/${childId}`),
      apiClient.get<CenterFilterOptions>('/centers/filter-options'),
      apiClient.get<CenterMatchResult>(`/children/${childId}/center-matches/latest`)
        .then((response) => response.data)
        .catch((requestError: unknown) => {
          if (isAxiosError(requestError) && requestError.response?.status === 404) return null
          throw requestError
        }),
    ])
      .then(([childResponse, optionsResponse, latest]) => {
        if (!mounted) return
        setChild(childResponse.data)
        setCities(optionsResponse.data.cities)
        setResult(latest)
        setCity(latest?.preferred_city ?? '')
        setDeliveryMode(latest?.delivery_mode ?? '')
      })
      .catch(() => {
        if (mounted) setError('تعذر فتح مطابقة المراكز أو لا تملك صلاحية الوصول إلى هذا الملف.')
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => { mounted = false }
  }, [childId])

  const runMatching = async () => {
    setMatching(true)
    setError('')
    try {
      const response = await apiClient.post<CenterMatchResult>(
        `/children/${childId}/center-matches`,
        {
          city: city || null,
          delivery_mode: deliveryMode || null,
        },
      )
      setResult(response.data)
    } catch {
      setError('تعذر إنشاء المطابقة الآن. حاولي مرة أخرى بعد قليل.')
    } finally {
      setMatching(false)
    }
  }

  if (loading) return <div className="loading-row"><div className="spinner" /> جاري تجهيز المطابقة...</div>
  if (!child) return <div className="prototype-empty-card"><h2>تعذر فتح الملف</h2><p>{error}</p><Link className="btn btn-primary" to="/dashboard">العودة للرئيسية</Link></div>

  return (
    <section className="matching-page">
      <Link className="matching-back" to={`/children/${child.id}`}>← العودة إلى ملف {child.preferred_name || child.first_name}</Link>

      <div className="matching-hero">
        <div>
          <span className="soft-kicker">مطابقة المراكز</span>
          <h1>خيارات مناسبة لاحتياجات {child.preferred_name || child.first_name}</h1>
          <p>يقارن وئام احتياجات الملف مع خدمات المراكز والفئات العمرية، ثم يعرض خيارات مناسبة وأسباب ظهورها.</p>
        </div>
        <span className="matching-hero-mark" aria-hidden="true">✦</span>
      </div>

      <div className="matching-safety-note">
        <span aria-hidden="true">i</span>
        <p>المطابقة تساعدك على تضييق الخيارات، ولا تعني اعتمادًا طبيًا أو ضمانًا لجودة المركز. تحققي من توفر الخدمة والمواعيد مباشرة مع المركز.</p>
      </div>

      <details className="matching-controls">
        <summary>
          <div>
            <span className="soft-kicker">تفضيلات اختيارية</span>
            <h2>تخصيص البحث</h2>
            <p>يمكنك تحديد المدينة أو طريقة تقديم الخدمة.</p>
          </div>
          <span className="matching-controls-toggle">عرض الخيارات <span aria-hidden="true">⌄</span></span>
        </summary>
        <div className="matching-control-fields">
          <label>
            <span>المدينة</span>
            <select value={city} onChange={(event) => setCity(event.target.value)}>
              <option value="">كل المدن</option>
              {cities.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label>
            <span>طريقة تقديم الخدمة</span>
            <select value={deliveryMode} onChange={(event) => setDeliveryMode(event.target.value as CenterMatchDeliveryMode | '')}>
              <option value="">كل الخيارات</option>
              <option value="in_person">حضوري</option>
              <option value="remote">عن بُعد</option>
              <option value="both">حضوري وعن بُعد</option>
            </select>
          </label>
          <button className="btn btn-primary matching-run" type="button" onClick={() => void runMatching()} disabled={matching}>
            {matching ? 'جاري تحليل الاحتياجات...' : result ? 'تحديث المطابقة' : 'عرض المراكز المناسبة'}
          </button>
        </div>
      </details>

      {error && <div className="alert alert-error" role="alert">{error}</div>}

      {!result ? (
        <div className="matching-empty">
          <span aria-hidden="true">✦</span>
          <h2>ابدئي المطابقة عند استعدادك</h2>
          <p>سيستخدم وئام معلومات الملف المصرح بها فقط، ولن يغيّر أي بيانات في ملف الطفل.</p>
          <button className="btn btn-primary" type="button" onClick={() => void runMatching()} disabled={matching}>بدء المطابقة</button>
        </div>
      ) : (
        <>
          <div className="matching-summary">
            <div>
              <span className="soft-kicker">خلاصة المطابقة</span>
              <h2>{result.matches.length ? matchingCountLabel(result.matches.length) : 'نتيجة المطابقة'}</h2>
              <p>{result.summary}</p>
            </div>
            <small>تم التحديث الآن</small>
          </div>

          <div className="matching-evidence">
            <article><span>معلومات الاحتياجات</span><strong>{result.profile_signals.length > 0 ? 'متوفرة' : 'تحتاج تحديث'}</strong></article>
            <article><span>التقارير المعتمدة</span><strong>{result.evidence.approved_reports_used}</strong></article>
            <article><span>الأهداف الحالية</span><strong>{result.evidence.active_goals_used}</strong></article>
            <article><span>العمر</span><strong>{result.child_age_years === null || result.child_age_years === undefined ? 'غير متاح' : `${result.child_age_years} سنة`}</strong></article>
          </div>

          {result.profile_signals.length > 0 && (
            <div className="matching-signals">
              <strong>الاحتياجات التي روعيت</strong>
              <div>{result.profile_signals.map((signal) => <span key={signal}>{signal}</span>)}</div>
            </div>
          )}

          {result.insufficient_data ? (
            <div className="matching-empty warning">
              <span aria-hidden="true">!</span>
              <h2>نحتاج معلومات أكثر لإجراء مطابقة موثوقة</h2>
              <p>أضيفي احتياجات الطفل أو الخدمات الحالية إلى الملف، أو اعتمدي تحليل تقرير ذي صلة، ثم أعيدي المطابقة.</p>
              <Link className="btn btn-outline" to={`/children/${child.id}`}>مراجعة ملف الطفل</Link>
            </div>
          ) : result.matches.length === 0 ? (
            <div className="matching-empty">
              <span aria-hidden="true">⌕</span>
              <h2>لم نجد تطابقًا ضمن الخيارات المحددة</h2>
              <p>جرّبي اختيار كل المدن أو تغيير طريقة تقديم الخدمة، ثم حدّثي المطابقة.</p>
            </div>
          ) : (
            <div className="matching-results">
              {result.matches.map((match) => (
                <article className="matching-card" key={match.center.id}>
                  <div className="matching-card-rank"><span>الخيار {match.rank}</span><small>{levelLabels[match.match_level]}</small></div>
                  <div className="matching-card-main">
                    <div className="matching-card-heading">
                      <div><span>{match.center.city}{match.center.region ? `، ${match.center.region}` : ''}</span><h2>{match.center.name}</h2></div>
                      <span className="matching-fit-label">مناسب بناءً على احتياجات الملف</span>
                    </div>
                    <div className="matching-card-tags">{match.matched_signals.map((signal) => <span key={signal}>{signal}</span>)}</div>
                    <div className="matching-card-details">
                      <div><h3>لماذا ظهر هذا المركز؟</h3><ul>{match.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div>
                    </div>
                    <div className="matching-card-footer">
                      <span>{match.center.offers_in_person ? 'حضوري' : ''}{match.center.offers_in_person && match.center.offers_remote ? ' • ' : ''}{match.center.offers_remote ? 'عن بُعد' : ''}</span>
                      <Link className="btn btn-outline" to={`/centers/${match.center.id}`}>عرض تفاصيل المركز</Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

        </>
      )}
    </section>
  )
}
