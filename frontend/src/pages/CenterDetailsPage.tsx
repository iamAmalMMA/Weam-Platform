import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { Center } from '../types'
import '../styles/centers.css'

function ageLabel(center: Center) {
  if (center.min_age_years == null && center.max_age_years == null) return 'جميع الأعمار'
  if (center.min_age_years != null && center.max_age_years != null) return `من ${center.min_age_years} إلى ${center.max_age_years} سنة`
  if (center.min_age_years != null) return `من ${center.min_age_years} سنة فأكثر`
  return `حتى ${center.max_age_years} سنة`
}

export default function CenterDetailsPage() {
  const { centerId } = useParams<{ centerId: string }>()
  const [center, setCenter] = useState<Center | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!centerId) return
    setLoading(true)
    apiClient.get<Center>(`/centers/${centerId}`)
      .then((response) => setCenter(response.data))
      .catch(() => setError('تعذر تحميل بيانات المركز. قد لا يكون متاحًا الآن.'))
      .finally(() => setLoading(false))
  }, [centerId])

  const toggleFavorite = async () => {
    if (!center || saving) return
    setSaving(true)
    setError('')
    try {
      if (center.is_favorite) {
        await apiClient.delete(`/centers/${center.id}/favorite`)
      } else {
        await apiClient.put(`/centers/${center.id}/favorite`)
      }
      setCenter({ ...center, is_favorite: !center.is_favorite })
    } catch {
      setError('تعذر تحديث المفضلة. حاول مرة أخرى.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="centers-loading"><div className="spinner" /> جاري تحميل بيانات المركز...</div>

  if (!center) {
    return <section className="center-detail-page"><div className="centers-empty"><span aria-hidden="true">!</span><h1>المركز غير متاح</h1><p>{error || 'لم نتمكن من العثور على بيانات هذا المركز.'}</p><Link className="btn btn-primary" to="/centers">العودة إلى المراكز والخدمات</Link></div></section>
  }

  const delivery: string[] = []
  if (center.offers_in_person) delivery.push('حضوري')
  if (center.offers_remote) delivery.push('عن بعد')

  return (
    <section className="center-detail-page">
      <Link className="center-detail-back" to="/centers">← العودة إلى المراكز والخدمات</Link>
      {error && <div className="alert alert-error centers-alert" role="alert">{error}</div>}

      <div className="center-detail-hero">
        <div className="center-detail-symbol" aria-hidden="true">⌂</div>
        <div className="center-detail-title">
          <div className="center-card-location"><span aria-hidden="true">⌖</span>{center.city}{center.region ? `، ${center.region}` : ''}</div>
          <h1>{center.name}</h1>
          <p>{center.description}</p>
          <div className="center-detail-modes">{delivery.map((item) => <span key={item}>{item}</span>)}</div>
        </div>
        <button type="button" className={`center-detail-favorite ${center.is_favorite ? 'active' : ''}`} onClick={() => void toggleFavorite()} disabled={saving} aria-pressed={center.is_favorite}>
          <span aria-hidden="true">{center.is_favorite ? '♥' : '♡'}</span>{center.is_favorite ? 'محفوظ في المفضلة' : 'حفظ في المفضلة'}
        </button>
      </div>

      <div className="center-detail-grid">
        <article className="center-detail-card wide">
          <div className="center-detail-card-title"><span aria-hidden="true">✦</span><h2>التخصصات والخدمات</h2></div>
          <div className="center-detail-columns">
            <div><h3>التخصصات</h3><div className="center-detail-tags">{center.specialties.map((item) => <span key={item}>{item}</span>)}</div></div>
            <div><h3>الخدمات</h3><ul>{center.services.map((item) => <li key={item}>{item}</li>)}</ul></div>
          </div>
        </article>

        <article className="center-detail-card">
          <div className="center-detail-card-title"><span aria-hidden="true">◌</span><h2>الأعمار والاحتياجات</h2></div>
          <strong className="center-age-range">{ageLabel(center)}</strong>
          <div className="center-detail-tags soft">{center.served_needs.map((item) => <span key={item}>{item}</span>)}</div>
        </article>

        <article className="center-detail-card">
          <div className="center-detail-card-title"><span aria-hidden="true">⌖</span><h2>الموقع وساعات العمل</h2></div>
          <dl className="center-detail-list"><div><dt>العنوان</dt><dd>{center.address}</dd></div><div><dt>ساعات العمل</dt><dd>{center.working_hours}</dd></div>{center.price_range && <div><dt>النطاق السعري</dt><dd>{center.price_range}</dd></div>}</dl>
        </article>

        {center.specialists.length > 0 && (
          <article className="center-detail-card wide">
            <div className="center-detail-card-title"><span aria-hidden="true">♧</span><h2>فريق المركز</h2></div>
            <div className="center-specialist-public-grid">
              {center.specialists.map((specialist) => (
                <div key={specialist.id}>
                  <span>{specialist.full_name.slice(0, 1)}</span>
                  <div><h3>{specialist.full_name}</h3><p>{specialist.professional_title} · {specialist.specialty}</p>{specialist.bio && <small>{specialist.bio}</small>}</div>
                </div>
              ))}
            </div>
          </article>
        )}

        <article className="center-contact-card wide">
          <div><span className="soft-kicker">التواصل</span><h2>تواصل مباشرة مع المركز</h2><p>تحقق من توفر الخدمة والمواعيد والتكلفة قبل الزيارة.</p></div>
          <div className="center-contact-actions">
            {center.phone && <a className="btn btn-primary" href={`tel:${center.phone.replace(/\s/g, '')}`}>اتصال: <bdi>{center.phone}</bdi></a>}
            {center.email && <a className="btn btn-white" href={`mailto:${center.email}`}>إرسال بريد إلكتروني</a>}
            {!center.phone && !center.email && <p className="muted">رقم التواصل غير متوفر من المصدر العام — راجعي القسم أعلاه لمزيد من التفاصيل.</p>}
          </div>
        </article>
      </div>
    </section>
  )
}
