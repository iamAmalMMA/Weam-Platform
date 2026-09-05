import { useEffect, useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import WeamLogo from './WeamLogo'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useSettings } from '../contexts/SettingsContext'

const roleLabelKeys = {
  guardian: 'role.guardian',
  care_provider: 'role.provider',
  center: 'role.center',
  admin: 'role.admin',
}

type ShellIconName = 'home' | 'centers' | 'provider' | 'messages' | 'invitations' | 'notifications' | 'add' | 'admin' | 'menu' | 'close' | 'logout' | 'settings'

type NavEntry = {
  to: string
  labelKey: string
  icon: ShellIconName
  badge?: number
}

function ShellIcon({ name }: { name: ShellIconName }) {
  const common = { width: 21, height: 21, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true }
  if (name === 'home') return <svg {...common}><path d="M3 11.5 12 4l9 7.5" /><path d="M5.5 10.5V21h13V10.5M9.5 21v-6h5v6" /></svg>
  if (name === 'centers') return <svg {...common}><path d="M4 21h16M6 21V8l6-4 6 4v13" /><path d="M9 11h.01M15 11h.01M9 15h.01M15 15h.01M10 21v-3h4v3" /></svg>
  if (name === 'provider') return <svg {...common}><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7V5h8v2M3 12h18M10 12v2h4v-2" /></svg>
  if (name === 'messages') return <svg {...common}><path d="M21 15a4 4 0 0 1-4 4H8l-5 2 1.5-4A7 7 0 0 1 3 12V8a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z" /><path d="M8 9h8M8 13h5" /></svg>
  if (name === 'invitations') return <svg {...common}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" /></svg>
  if (name === 'notifications') return <svg {...common}><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>
  if (name === 'add') return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 8v8M8 12h8" /></svg>
  if (name === 'admin') return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>
  if (name === 'menu') return <svg {...common}><path d="M4 7h16M4 12h16M4 17h16" /></svg>
  if (name === 'close') return <svg {...common}><path d="m6 6 12 12M18 6 6 18" /></svg>
  if (name === 'settings') return <svg {...common}><circle cx="12" cy="12" r="3.2" /><path d="M12 2.5v3M12 18.5v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2.5 12h3M18.5 12h3M4.9 19.1 7 17M17 7l2.1-2.1" /></svg>
  return <svg {...common}><path d="M10 17l5-5-5-5M15 12H3" /><path d="M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4" /></svg>
}

function pageTitle(pathname: string, t: (key: string) => string) {
  if (pathname.startsWith('/admin')) return t('nav.admin')
  if (pathname.startsWith('/provider/center')) return 'إدارة ملف المركز'
  if (pathname.startsWith('/provider')) return t('nav.provider')
  if (pathname.startsWith('/centers/')) return 'تفاصيل المركز'
  if (pathname.startsWith('/centers')) return t('nav.centers')
  if (pathname.startsWith('/messages') || pathname.includes('/communication')) return t('nav.messages')
  if (pathname.startsWith('/notifications')) return t('nav.notifications')
  if (pathname.startsWith('/invitations')) return t('nav.invitations')
  if (pathname.includes('/center-matches')) return 'مطابقة المراكز'
  if (pathname.includes('/care-team')) return 'فريق الرعاية'
  if (pathname.includes('/reports')) return 'التقارير'
  if (pathname.includes('/goals')) return 'الأهداف'
  if (pathname.includes('/follow-ups')) return 'المتابعات'
  if (pathname.includes('/timeline')) return 'الخط الزمني'
  if (pathname.includes('/voice-notes')) return 'الملاحظات الصوتية'
  if (pathname.includes('/assistant')) return 'مساعد وئام'
  if (pathname.startsWith('/children/new')) return t('nav.addChild')
  if (pathname.startsWith('/children/')) return 'ملف الطفل'
  return t('nav.home')
}

export default function AppShell() {
  const { user, logout } = useAuth()
  const { t } = useSettings()
  const navigate = useNavigate()
  const location = useLocation()
  const [unread, setUnread] = useState(0)
  const [chatUnread, setChatUnread] = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    let mounted = true
    const load = () => {
      apiClient.get<{ count: number }>('/notifications/unread-count')
        .then((response) => {
          if (mounted) setUnread(response.data.count)
        })
        .catch(() => undefined)
      apiClient.get<{ count: number }>('/chat/unread-count')
        .then((response) => {
          if (mounted) setChatUnread(response.data.count)
        })
        .catch(() => undefined)
    }
    load()
    const timer = window.setInterval(load, 30000)
    const refresh = () => load()
    window.addEventListener('weam:notifications-changed', refresh)
    window.addEventListener('weam:chat-changed', refresh)
    return () => {
      mounted = false
      window.clearInterval(timer)
      window.removeEventListener('weam:notifications-changed', refresh)
      window.removeEventListener('weam:chat-changed', refresh)
    }
  }, [])

  useEffect(() => setSidebarOpen(false), [location.pathname])

  const navEntries = useMemo<NavEntry[]>(() => {
    if (user?.role === 'admin') {
      return [
        { to: '/admin', labelKey: 'nav.admin', icon: 'admin' },
        { to: '/notifications', labelKey: 'nav.notifications', icon: 'notifications', badge: unread },
        { to: '/settings', labelKey: 'nav.settings', icon: 'settings' },
      ]
    }
    const entries: NavEntry[] = [
      { to: '/dashboard', labelKey: 'nav.home', icon: 'home' },
      { to: '/centers', labelKey: 'nav.centers', icon: 'centers' },
    ]
    if (user?.role === 'care_provider' || user?.role === 'center') entries.push({ to: '/provider', labelKey: 'nav.provider', icon: 'provider' })
    entries.push(
      { to: '/messages', labelKey: 'nav.messages', icon: 'messages', badge: chatUnread },
      { to: '/invitations', labelKey: 'nav.invitations', icon: 'invitations' },
    )
    if (user?.role === 'guardian') entries.push({ to: '/children/new', labelKey: 'nav.addChild', icon: 'add' })
    entries.push(
      { to: '/notifications', labelKey: 'nav.notifications', icon: 'notifications', badge: unread },
      { to: '/settings', labelKey: 'nav.settings', icon: 'settings' },
    )
    return entries
  }, [chatUnread, unread, user?.role])

  const mobileEntries = useMemo(() => {
    if (user?.role === 'admin') return navEntries
    const preferred = user?.role === 'guardian'
      ? ['/dashboard', '/centers', '/children/new', '/messages', '/notifications']
      : ['/dashboard', '/centers', '/provider', '/messages', '/notifications']
    return preferred.map((to) => navEntries.find((entry) => entry.to === to)).filter((entry): entry is NavEntry => Boolean(entry))
  }, [navEntries, user?.role])

  const signOut = () => {
    logout()
    navigate('/')
  }

  const initial = user?.full_name?.trim().slice(0, 1) || 'و'
  const roleLabel = user ? t(roleLabelKeys[user.role]) : ''

  return (
    <div className="m9-app-shell">
      <button className={`m9-sidebar-overlay ${sidebarOpen ? 'visible' : ''}`} type="button" aria-label="إغلاق القائمة" onClick={() => setSidebarOpen(false)} />

      <aside className={`m9-sidebar ${sidebarOpen ? 'open' : ''}`} aria-label="التنقل الرئيسي">
        <div className="m9-sidebar-head">
          <WeamLogo to="/dashboard" compact />
          <button className="m9-sidebar-close" type="button" aria-label="إغلاق القائمة" onClick={() => setSidebarOpen(false)}><ShellIcon name="close" /></button>
        </div>
        <div className="m9-account-card">
          <span className="m9-account-avatar">{initial}</span>
          <div><strong>{user?.full_name}</strong><small>{roleLabel}</small></div>
        </div>
        <nav className="m9-side-nav">
          {navEntries.map((entry) => (
            <NavLink key={entry.to} to={entry.to} className={({ isActive }) => isActive ? 'active' : undefined}>
              <span className="m9-nav-icon"><ShellIcon name={entry.icon} /></span>
              <span>{t(entry.labelKey)}</span>
              {Boolean(entry.badge) && <b>{entry.badge! > 99 ? '99+' : entry.badge}</b>}
            </NavLink>
          ))}
        </nav>
        <div className="m9-sidebar-spacer" />
        <div className="m9-privacy-note"><strong>{t('nav.privacyTitle')}</strong><span>{t('nav.privacyBody')}</span></div>
        <button className="m9-signout-button" type="button" onClick={signOut}><ShellIcon name="logout" /> {t('nav.signOut')}</button>
      </aside>

      <div className="m9-app-main">
        <header className="m9-topbar">
          <button className="m9-menu-button" type="button" aria-label="فتح القائمة" onClick={() => setSidebarOpen(true)}><ShellIcon name="menu" /></button>
          <div className="m9-topbar-title"><span>Weam</span><strong>{pageTitle(location.pathname, t)}</strong></div>
          <div className="m9-topbar-actions">
            <NavLink className="m9-topbar-notifications" to="/notifications" aria-label={`التنبيهات غير المقروءة ${unread}`}>
              <ShellIcon name="notifications" />
              {unread > 0 && <b>{unread > 99 ? '99+' : unread}</b>}
            </NavLink>
            <div className="m9-topbar-profile"><span>{initial}</span><div><strong>{user?.full_name}</strong><small>{roleLabel}</small></div></div>
          </div>
        </header>
        <main className="m9-page-wrap"><Outlet /></main>
      </div>

      <nav className="m9-mobile-bottom-nav" aria-label="التنقل السفلي">
        {mobileEntries.map((entry) => (
          <NavLink key={entry.to} to={entry.to} className={entry.icon === 'add' ? 'm9-mobile-primary' : undefined}>
            <span><ShellIcon name={entry.icon} />{Boolean(entry.badge) && <b>{entry.badge! > 9 ? '9+' : entry.badge}</b>}</span>
            <small>{entry.icon === 'centers' ? t('nav.centers').split(' ')[0] : t(entry.labelKey)}</small>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
