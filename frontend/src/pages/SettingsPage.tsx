import { useAuth } from '../contexts/AuthContext'
import { useSettings, type Language, type TextScale, type ThemeMode } from '../contexts/SettingsContext'
import '../styles/settings.css'

const THEME_OPTIONS: { value: ThemeMode; labelKey: string; hintKey: string; icon: string }[] = [
  { value: 'light', labelKey: 'settings.theme.light', hintKey: 'settings.theme.lightHint', icon: '☀️' },
  { value: 'dark', labelKey: 'settings.theme.dark', hintKey: 'settings.theme.darkHint', icon: '🌙' },
]

const TEXT_SCALE_OPTIONS: { value: TextScale; labelKey: string; sample: string }[] = [
  { value: 'normal', labelKey: 'settings.textSize.normal', sample: '18px' },
  { value: 'large', labelKey: 'settings.textSize.large', sample: '21px' },
  { value: 'xlarge', labelKey: 'settings.textSize.xlarge', sample: '24px' },
]

const LANGUAGE_OPTIONS: { value: Language; labelKey: string; icon: string }[] = [
  { value: 'ar', labelKey: 'settings.language.ar', icon: '🇸🇦' },
  { value: 'en', labelKey: 'settings.language.en', icon: '🇬🇧' },
]

export default function SettingsPage() {
  const { user } = useAuth()
  const { theme, setTheme, textScale, setTextScale, language, setLanguage, t } = useSettings()

  return (
    <section className="m3-page settings-page">
      <div className="m3-hero">
        <div>
          <span className="soft-kicker">{t('settings.kicker')}</span>
          <h1>{t('settings.title')}</h1>
          <p>{t('settings.subtitle')}</p>
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>{t('settings.account')}</h2>
          <p>{t('settings.accountSubtitle')}</p>
        </div>
        <dl className="settings-account-grid">
          <div><dt>{t('settings.name')}</dt><dd>{user?.full_name || '—'}</dd></div>
          <div><dt>{t('settings.email')}</dt><dd>{user?.email || '—'}</dd></div>
        </dl>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>{t('settings.appearance')}</h2>
          <p>{t('settings.appearanceSubtitle')}</p>
        </div>
        <div className="settings-option-grid" role="radiogroup" aria-label={t('settings.appearance')}>
          {THEME_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={theme === option.value}
              className={`settings-option ${theme === option.value ? 'active' : ''}`}
              onClick={() => setTheme(option.value)}
            >
              <span className="settings-option-icon" aria-hidden="true">{option.icon}</span>
              <strong>{t(option.labelKey)}</strong>
              <small>{t(option.hintKey)}</small>
            </button>
          ))}
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>{t('settings.textSize')}</h2>
          <p>{t('settings.textSizeSubtitle')}</p>
        </div>
        <div className="settings-option-grid settings-text-scale-grid" role="radiogroup" aria-label={t('settings.textSize')}>
          {TEXT_SCALE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={textScale === option.value}
              className={`settings-option ${textScale === option.value ? 'active' : ''}`}
              onClick={() => setTextScale(option.value)}
            >
              <span className="settings-text-sample" style={{ fontSize: option.sample }} aria-hidden="true">Aأ</span>
              <strong>{t(option.labelKey)}</strong>
            </button>
          ))}
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>{t('settings.language')}</h2>
          <p>{t('settings.languageSubtitle')}</p>
        </div>
        <div className="settings-option-grid settings-language-grid" role="radiogroup" aria-label={t('settings.language')}>
          {LANGUAGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={language === option.value}
              className={`settings-option ${language === option.value ? 'active' : ''}`}
              onClick={() => setLanguage(option.value)}
            >
              <span className="settings-option-icon" aria-hidden="true">{option.icon}</span>
              <strong>{t(option.labelKey)}</strong>
            </button>
          ))}
        </div>
        <p className="settings-language-note">{t('settings.language.note')}</p>
      </div>
    </section>
  )
}
