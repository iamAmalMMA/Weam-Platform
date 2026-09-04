import { useAuth } from '../contexts/AuthContext'
import { useSettings, type TextScale, type ThemeMode } from '../contexts/SettingsContext'
import '../styles/settings.css'

const THEME_OPTIONS: { value: ThemeMode; label: string; hint: string; icon: string }[] = [
  { value: 'light', label: 'فاتح', hint: 'مظهر فاتح دائمًا', icon: '☀️' },
  { value: 'dark', label: 'داكن', hint: 'مظهر داكن دائمًا', icon: '🌙' },
  { value: 'system', label: 'حسب الجهاز', hint: 'يتبع إعداد جهازك تلقائيًا', icon: '🖥️' },
]

const TEXT_SCALE_OPTIONS: { value: TextScale; label: string; sample: string }[] = [
  { value: 'normal', label: 'عادي', sample: '18px' },
  { value: 'large', label: 'كبير', sample: '21px' },
  { value: 'xlarge', label: 'أكبر', sample: '24px' },
]

export default function SettingsPage() {
  const { user } = useAuth()
  const { theme, setTheme, textScale, setTextScale } = useSettings()

  return (
    <section className="m3-page settings-page">
      <div className="m3-hero">
        <div>
          <span className="soft-kicker">الإعدادات</span>
          <h1>تفضيلاتك في وئام</h1>
          <p>خصّصي مظهر التطبيق وحجم الخط بما يناسبك. هذه الإعدادات تُحفظ على جهازك فقط.</p>
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>الحساب</h2>
          <p>معلومات حسابك الحالي.</p>
        </div>
        <dl className="settings-account-grid">
          <div><dt>الاسم</dt><dd>{user?.full_name || '—'}</dd></div>
          <div><dt>البريد الإلكتروني</dt><dd>{user?.email || '—'}</dd></div>
        </dl>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>المظهر</h2>
          <p>اختاري بين المظهر الفاتح والداكن، أو اتركيه يتبع إعداد جهازك.</p>
        </div>
        <div className="settings-option-grid" role="radiogroup" aria-label="المظهر">
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
              <strong>{option.label}</strong>
              <small>{option.hint}</small>
            </button>
          ))}
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <h2>حجم النص والأيقونات</h2>
          <p>لتسهيل القراءة، يمكنك تكبير النصوص والأيقونات في كل صفحات التطبيق.</p>
        </div>
        <div className="settings-option-grid settings-text-scale-grid" role="radiogroup" aria-label="حجم النص">
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
              <strong>{option.label}</strong>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
