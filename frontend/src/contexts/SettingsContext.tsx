import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type ThemeMode = 'system' | 'light' | 'dark'
export type TextScale = 'normal' | 'large' | 'xlarge'

const THEME_KEY = 'weam_theme'
const TEXT_SCALE_KEY = 'weam_text_scale'

const ZOOM_BY_SCALE: Record<TextScale, string> = {
  normal: '1.08',
  large: '1.22',
  xlarge: '1.38',
}

interface SettingsContextValue {
  theme: ThemeMode
  setTheme: (theme: ThemeMode) => void
  textScale: TextScale
  setTextScale: (scale: TextScale) => void
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined)

function readTheme(): ThemeMode {
  const stored = localStorage.getItem(THEME_KEY)
  return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system'
}

function readTextScale(): TextScale {
  const stored = localStorage.getItem(TEXT_SCALE_KEY)
  return stored === 'normal' || stored === 'large' || stored === 'xlarge' ? stored : 'normal'
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(readTheme)
  const [textScale, setTextScaleState] = useState<TextScale>(readTextScale)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', theme)
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    document.documentElement.style.setProperty('--a11y-zoom', ZOOM_BY_SCALE[textScale])
    localStorage.setItem(TEXT_SCALE_KEY, textScale)
  }, [textScale])

  const value = useMemo<SettingsContextValue>(() => ({
    theme,
    setTheme: setThemeState,
    textScale,
    setTextScale: setTextScaleState,
  }), [theme, textScale])

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within a SettingsProvider')
  return ctx
}
