import { FormEvent, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AxiosError } from 'axios'
import WeamLogo from '../components/WeamLogo'
import { useAuth } from '../contexts/AuthContext'
import { useSettings } from '../contexts/SettingsContext'

function errorMessage(error: unknown) {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (detail === 'Invalid email or password') return 'البريد الإلكتروني أو كلمة المرور غير صحيحة.'
    if (error.response?.status === 429) return 'محاولات كثيرة غير ناجحة. يرجى المحاولة لاحقًا بعد بضع دقائق.'
    if (detail === 'Account is disabled') return 'هذا الحساب معطّل حاليًا. يرجى التواصل مع الدعم.'
  }
  return 'تعذر تسجيل الدخول. حاولي مرة أخرى.'
}

export default function LoginPage() {
  const { login } = useAuth()
  const { t } = useSettings()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Deliberately no "already logged in → redirect to dashboard" guard here:
  // visiting /login while authenticated (e.g. to try a different demo
  // account) should show the form, not silently bounce away before the new
  // credentials can be submitted.

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await login(email, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from || '/dashboard', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="prototype-auth-page">
      <section className="prototype-auth-visual">
        <WeamLogo to="/" />
        <div className="auth-scene">
          <div className="auth-scene-glow" />
          <img src="/weam-family.webp" alt="ولي أمر وفريق الرعاية يلتفّون حول طفلة ضمن منصة وئام" />
        </div>
      </section>

      <section className="prototype-auth-form-wrap">
        <div className="prototype-auth-form">
          <div className="mobile-logo"><WeamLogo compact /></div>
          <span className="soft-kicker">{t('login.kicker')}</span>
          <h2>{t('login.title')}</h2>
          <p className="muted auth-intro">{t('login.subtitle')}</p>

          <form className="form-stack" onSubmit={submit}>
            <label>{t('login.email')}<input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@example.com" /></label>
            <label>{t('login.password')}<input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" /></label>
            {error && <div className="alert alert-error">{error}</div>}
            <button className="btn btn-primary btn-block btn-large" disabled={submitting}>{submitting ? t('login.submitting') : t('login.submit')}</button>
          </form>

          <p className="auth-switch">{t('login.noAccount')} <Link to="/register">{t('login.createOne')}</Link></p>
          <Link className="back-home-link" to="/">{t('login.backHome')}</Link>
        </div>
      </section>
    </main>
  )
}
