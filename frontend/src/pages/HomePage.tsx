import { Link, Navigate } from 'react-router-dom'
import WeamConnector from '../components/WeamConnector'
import WeamLogo from '../components/WeamLogo'
import { useAuth } from '../contexts/AuthContext'
import { useSettings } from '../contexts/SettingsContext'

export default function HomePage() {
  const { user, loading } = useAuth()
  const { t } = useSettings()
  if (!loading && user) return <Navigate to="/dashboard" replace />

  return (
    <main className="welcome-page">
      <WeamConnector />
      <div className="sky-bubble bubble-one" />
      <div className="sky-bubble bubble-two" />

      <header className="welcome-nav">
        <WeamLogo to="/" compact />
      </header>

      <section className="welcome-hero">
        <div className="welcome-copy">
          <h1>{t('home.h1.part1')}<br />{t('home.h1.part2')} <span>{t('home.h1.part3')}</span></h1>
          <div className="welcome-actions">
            <Link className="btn btn-primary btn-large" to="/register">{t('home.cta.register')}</Link>
            <Link className="btn btn-white btn-large" to="/login">{t('home.cta.login')}</Link>
          </div>
        </div>

        <div className="welcome-art" aria-label="عائلة وفريق رعاية يلتفّون حول طفلة ضمن منصة وئام">
          <div className="art-glow" />
          <img className="art-illustration" src="/weam-family.webp" alt="ولي أمر وفريق الرعاية يلتفّون حول طفلة ضمن منصة وئام" />
        </div>
      </section>

      <section className="welcome-benefits">
        <article>
          <span>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
              <path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5A1.5 1.5 0 0 1 7 3.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
              <path d="M14 3.5V8h4M9 12.5h6M9 15.5h6M9 9.5h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </span>
          <strong>{t('home.benefit.reports')}</strong>
        </article>
        <article>
          <span>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="8.5" stroke="currentColor" strokeWidth="1.6" />
              <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.6" />
              <circle cx="12" cy="12" r="1.4" fill="currentColor" />
            </svg>
          </span>
          <strong>{t('home.benefit.goals')}</strong>
        </article>
        <article>
          <span>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
              <circle cx="9" cy="8.5" r="2.6" stroke="currentColor" strokeWidth="1.6" />
              <path d="M4 19c0-3 2.2-5 5-5s5 2 5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              <circle cx="17" cy="9" r="2.1" stroke="currentColor" strokeWidth="1.6" />
              <path d="M15.5 19c.2-2.4 1.7-4.1 3.9-4.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </span>
          <strong>{t('home.benefit.team')}</strong>
        </article>
      </section>
    </main>
  )
}
