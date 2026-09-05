import { FormEvent, useCallback, useState } from 'react'
import { AxiosError } from 'axios'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import GoogleSignInButton from '../components/GoogleSignInButton'
import WeamLogo from '../components/WeamLogo'
import { useAuth } from '../contexts/AuthContext'
import { useSettings } from '../contexts/SettingsContext'
import type { UserRole } from '../types'

const roles: Array<{ value: UserRole; titleKey: string; copyKey: string; icon: string }> = [
  { value: 'guardian', titleKey: 'register.role.guardian', copyKey: 'register.role.guardian.copy', icon: '♡' },
  { value: 'care_provider', titleKey: 'register.role.provider', copyKey: 'register.role.provider.copy', icon: '✦' },
  { value: 'center', titleKey: 'register.role.center', copyKey: 'register.role.center.copy', icon: '⌂' },
]

function errorMessage(error: unknown) {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (detail === 'Email is already registered') return 'يوجد حساب مسجل بهذا البريد الإلكتروني.'
    if (detail) return detail
  }
  return 'تعذر إنشاء الحساب. تحققي من البيانات وحاولي مرة أخرى.'
}

export default function RegisterPage() {
  const { user, register, loginWithGoogleCredential } = useAuth()
  const { t } = useSettings()
  const navigate = useNavigate()
  const [role, setRole] = useState<UserRole>('guardian')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [specialty, setSpecialty] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await register({ email, full_name: fullName, password, role, provider_specialty: role === 'care_provider' ? specialty : undefined })
      navigate(role === 'guardian' ? '/children/new' : '/provider', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const google = useCallback(async (credential: string) => {
    setError('')
    try {
      await loginWithGoogleCredential(credential, role, role === 'care_provider' ? specialty : undefined)
      navigate(role === 'guardian' ? '/children/new' : '/provider', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    }
  }, [loginWithGoogleCredential, navigate, role, specialty])

  return (
    <main className="register-page prototype-register-page">
      <header className="prototype-simple-header">
        <WeamLogo to="/" compact />
        <p>{t('register.haveAccount')} <Link to="/login">{t('register.signIn')}</Link></p>
      </header>

      <section className="prototype-register-shell">
        <div className="section-heading centered">
          <span className="soft-kicker">{t('register.kicker')}</span>
          <h1>{t('register.title')}</h1>
          <p>{t('register.subtitle')}</p>
        </div>

        <div className="prototype-role-grid">
          {roles.map((item) => (
            <button type="button" key={item.value} className={`prototype-role-card ${role === item.value ? 'selected' : ''}`} onClick={() => setRole(item.value)} aria-pressed={role === item.value}>
              <span className="prototype-role-icon">{item.icon}</span>
              <strong>{t(item.titleKey)}</strong>
              <small>{t(item.copyKey)}</small>
              <span className="role-check">✓</span>
            </button>
          ))}
        </div>

        <form className="prototype-register-form" onSubmit={submit}>
          <div className="form-grid two">
            <label>{t('register.fullName')}<input required minLength={2} value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder={t('register.fullName')} /></label>
            <label>{t('register.email')}<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@example.com" /></label>
          </div>
          {role === 'care_provider' && <label>{t('register.specialty')}<input required value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="مثال: تخاطب، سمعيات، علاج وظيفي" /></label>}
          <label>{t('register.password')}<input required type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="8 أحرف على الأقل" /></label>
          {role !== 'guardian' && <div className="notice"><strong>ملاحظة التحقق</strong><p>يبدأ الحساب بحالة «غير موثّق» إلى أن تتم مراجعته إداريًا.</p></div>}
          {error && <div className="alert alert-error">{error}</div>}
          <button className="btn btn-primary btn-block btn-large" disabled={submitting}>{submitting ? t('register.submitting') : t('register.submit')}</button>
          <div className="divider"><span>{t('register.or')}</span></div>
          <GoogleSignInButton onCredential={google} />
        </form>
      </section>
    </main>
  )
}
