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
        <div className="welcome-nav-actions">
          <Link className="btn btn-outline" to="/login">{t('nav.login')}</Link>
          <Link className="btn btn-primary" to="/register">{t('nav.register')}</Link>
        </div>
      </header>

      <section className="welcome-hero">
        <div className="welcome-copy">
          <span className="soft-kicker">{t('home.kicker')}</span>
          <h1>{t('home.h1.part1')} <span>{t('home.h1.part2')}</span></h1>
          <div className="welcome-actions">
            <Link className="btn btn-primary btn-large" to="/register">{t('home.cta.register')}</Link>
            <Link className="btn btn-white btn-large" to="/login">{t('home.cta.login')}</Link>
          </div>
          <div className="privacy-pill">{t('home.privacy')}</div>
        </div>

        <div className="welcome-art" aria-label="واجهة مستوحاة من بروتوتايب وئام">
          <div className="scene-frame">
            <img src="/prototype-girl.png" alt="طفلة ضمن الهوية البصرية لبروتوتايب وئام" />
            <div className="scene-wash" />
          </div>
        </div>
      </section>

      <section className="welcome-benefits">
        <article><span>📄</span><strong>{t('home.benefit.reports')}</strong></article>
        <article><span>🎯</span><strong>{t('home.benefit.goals')}</strong></article>
        <article><span>👥</span><strong>{t('home.benefit.team')}</strong></article>
      </section>
    </main>
  )
}
