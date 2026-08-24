import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { apiClient } from '../api/client'
import TagEditor from '../components/TagEditor'
import type { CenterSpecialist, ManagedCenter } from '../types'
import '../styles/provider-portal.css'

interface CenterForm {
  name: string
  description: string
  city: string
  region: string
  address: string
  specialties: string[]
  services: string[]
  served_needs: string[]
  min_age_years: string
  max_age_years: string
  offers_in_person: boolean
  offers_remote: boolean
  phone: string
  email: string
  working_hours: string
  price_range: string
}

const emptyForm: CenterForm = {
  name: '', description: '', city: '', region: '', address: '', specialties: [], services: [], served_needs: [],
  min_age_years: '', max_age_years: '', offers_in_person: true, offers_remote: false, phone: '', email: '', working_hours: '', price_range: '',
}

const toForm = (center: ManagedCenter): CenterForm => ({
  name: center.name,
  description: center.description,
  city: center.city,
  region: center.region || '',
  address: center.address,
  specialties: center.specialties,
  services: center.services,
  served_needs: center.served_needs,
  min_age_years: center.min_age_years?.toString() || '',
  max_age_years: center.max_age_years?.toString() || '',
  offers_in_person: center.offers_in_person,
  offers_remote: center.offers_remote,
  phone: center.phone,
  email: center.email || '',
  working_hours: center.working_hours,
  price_range: center.price_range || '',
})

export default function CenterManagementPage() {
  const [center, setCenter] = useState<ManagedCenter | null>(null)
  const [form, setForm] = useState<CenterForm>(emptyForm)
  const [specialists, setSpecialists] = useState<CenterSpecialist[]>([])
  const [specialist, setSpecialist] = useState({ full_name: '', professional_title: '', specialty: '', bio: '' })
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const loadSpecialists = () => apiClient.get<CenterSpecialist[]>('/provider/center/specialists').then((response) => setSpecialists(response.data))

  useEffect(() => {
    apiClient.get<ManagedCenter>('/provider/center')
      .then((response) => {
        setCenter(response.data)
        setForm(toForm(response.data))
        return loadSpecialists()
      })
      .catch((requestError: unknown) => {
        if (!(isAxiosError(requestError) && requestError.response?.status === 404)) setError('تعذر تحميل ملف المركز.')
      })
      .finally(() => setLoading(false))
  }, [])

  const setField = <K extends keyof CenterForm>(field: K, value: CenterForm[K]) => setForm((current) => ({ ...current, [field]: value }))

  const saveCenter = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    const payload = {
      ...form,
      region: form.region || null,
      email: form.email || null,
      price_range: form.price_range || null,
      min_age_years: form.min_age_years ? Number(form.min_age_years) : null,
      max_age_years: form.max_age_years ? Number(form.max_age_years) : null,
    }
    try {
      const response = center
        ? await apiClient.patch<ManagedCenter>('/provider/center', payload)
        : await apiClient.post<ManagedCenter>('/provider/center', payload)
      setCenter(response.data)
      setForm(toForm(response.data))
      setMessage(center ? 'تم حفظ بيانات المركز وإرسال التغييرات للمراجعة.' : 'تم إنشاء ملف المركز وإرساله للمراجعة.')
      if (!center) await loadSpecialists()
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || 'تعذر حفظ بيانات المركز.')
    } finally {
      setBusy(false)
    }
  }

  const addSpecialist = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await apiClient.post('/provider/center/specialists', specialist)
      setSpecialist({ full_name: '', professional_title: '', specialty: '', bio: '' })
      await loadSpecialists()
    } catch {
      setError('تعذر إضافة المختص.')
    } finally {
      setBusy(false)
    }
  }

  const deleteSpecialist = async (id: string) => {
    if (!window.confirm('هل تريد إزالة المختص من ملف المركز؟')) return
    await apiClient.delete(`/provider/center/specialists/${id}`)
    await loadSpecialists()
  }

  if (loading) return <div className="loading-row"><div className="spinner" /> جاري تحميل ملف المركز...</div>

  return (
    <section className="center-management-page">
      <div className="provider-page-heading"><div><Link to="/provider">← العودة لمساحة مقدم الخدمة</Link><span className="soft-kicker">ملف المركز</span><h1>{center ? 'إدارة بيانات المركز' : 'إنشاء ملف المركز'}</h1><p>هذه البيانات تظهر للأسر بعد مراجعة إدارة وئام واعتمادها.</p></div>{center && <span className={`status-pill ${center.verification_status === 'verified' ? 'success' : 'warning'}`}>{center.verification_status === 'verified' ? 'موثّق' : center.verification_status === 'rejected' ? 'يحتاج تعديل' : 'قيد المراجعة'}</span>}</div>
      {center?.verification_note && <div className="notice"><strong>ملاحظة المراجعة</strong><p>{center.verification_note}</p></div>}
      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <form className="provider-center-form" onSubmit={saveCenter}>
        <div className="provider-form-section"><h2>المعلومات الأساسية</h2><div className="form-grid two"><label>اسم المركز<input required minLength={2} value={form.name} onChange={(event) => setField('name', event.target.value)} /></label><label>المدينة<input required value={form.city} onChange={(event) => setField('city', event.target.value)} /></label><label>المنطقة<input value={form.region} onChange={(event) => setField('region', event.target.value)} /></label><label>العنوان<input required value={form.address} onChange={(event) => setField('address', event.target.value)} /></label></div><label>نبذة عن المركز<textarea required minLength={10} rows={4} value={form.description} onChange={(event) => setField('description', event.target.value)} /></label></div>
        <div className="provider-form-section"><h2>الخدمات والاحتياجات</h2><div className="provider-tags-grid"><TagEditor label="التخصصات" value={form.specialties} onChange={(value) => setField('specialties', value)} /><TagEditor label="الخدمات" value={form.services} onChange={(value) => setField('services', value)} /><TagEditor label="الاحتياجات التي يخدمها المركز" value={form.served_needs} onChange={(value) => setField('served_needs', value)} /></div><div className="form-grid two"><label>أقل عمر<input type="number" min="0" max="100" value={form.min_age_years} onChange={(event) => setField('min_age_years', event.target.value)} /></label><label>أعلى عمر<input type="number" min="0" max="100" value={form.max_age_years} onChange={(event) => setField('max_age_years', event.target.value)} /></label></div><div className="provider-check-row"><label><input type="checkbox" checked={form.offers_in_person} onChange={(event) => setField('offers_in_person', event.target.checked)} /> حضوري</label><label><input type="checkbox" checked={form.offers_remote} onChange={(event) => setField('offers_remote', event.target.checked)} /> عن بُعد</label></div></div>
        <div className="provider-form-section"><h2>التواصل والعمل</h2><div className="form-grid two"><label>رقم التواصل<input className="provider-ltr-field" dir="ltr" required value={form.phone} onChange={(event) => setField('phone', event.target.value)} /></label><label>البريد الإلكتروني<input className="provider-ltr-field" dir="ltr" type="email" value={form.email} onChange={(event) => setField('email', event.target.value)} /></label><label>ساعات العمل<input required value={form.working_hours} onChange={(event) => setField('working_hours', event.target.value)} /></label><label>النطاق السعري<input value={form.price_range} onChange={(event) => setField('price_range', event.target.value)} /></label></div></div>
        <div className="provider-form-actions"><button className="btn btn-primary" disabled={busy}>{busy ? 'جاري الحفظ...' : center ? 'حفظ التغييرات' : 'إنشاء ملف المركز'}</button></div>
      </form>

      {center && (
        <section className="provider-specialists-section"><div className="provider-section-heading"><div><span className="soft-kicker">فريق المركز</span><h2>المختصون</h2></div><small>بيانات مهنية مختصرة لفريق المركز.</small></div><form className="specialist-create-form" onSubmit={addSpecialist}><input required placeholder="اسم المختص" value={specialist.full_name} onChange={(event) => setSpecialist((current) => ({ ...current, full_name: event.target.value }))} /><input required placeholder="المسمى المهني" value={specialist.professional_title} onChange={(event) => setSpecialist((current) => ({ ...current, professional_title: event.target.value }))} /><input required placeholder="التخصص" value={specialist.specialty} onChange={(event) => setSpecialist((current) => ({ ...current, specialty: event.target.value }))} /><button className="btn btn-primary" disabled={busy}>إضافة مختص</button></form>{!specialists.length ? <div className="provider-inline-empty">لم تتم إضافة مختصين بعد.</div> : <div className="specialist-grid">{specialists.map((item) => <article key={item.id}><span>{item.full_name.slice(0, 1)}</span><div><h3>{item.full_name}</h3><p>{item.professional_title} · {item.specialty}</p></div><button className="specialist-remove-button" type="button" onClick={() => void deleteSpecialist(item.id)}>إزالة المختص</button></article>)}</div>}</section>
      )}
    </section>
  )
}
