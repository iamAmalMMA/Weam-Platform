import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { translate, type Language } from '../i18n/translations'

export type ThemeMode = 'light' | 'dark'
export type TextScale = 'normal' | 'large' | 'xlarge'
export type { Language }

const THEME_KEY = 'weam_theme'
const TEXT_SCALE_KEY = 'weam_text_scale'
const LANGUAGE_KEY = 'weam_language'

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
  language: Language
  setLanguage: (language: Language) => void
  t: (key: string) => string
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined)

function readTheme(): ThemeMode {
  const stored = localStorage.getItem(THEME_KEY)
  return stored === 'light' || stored === 'dark' ? stored : 'light'
}

function readTextScale(): TextScale {
  const stored = localStorage.getItem(TEXT_SCALE_KEY)
  return stored === 'normal' || stored === 'large' || stored === 'xlarge' ? stored : 'normal'
}

function readLanguage(): Language {
  const stored = localStorage.getItem(LANGUAGE_KEY)
  return stored === 'en' ? 'en' : 'ar'
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(readTheme)
  const [textScale, setTextScaleState] = useState<TextScale>(readTextScale)
  const [language, setLanguageState] = useState<Language>(readLanguage)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    document.documentElement.style.setProperty('--a11y-zoom', ZOOM_BY_SCALE[textScale])
    localStorage.setItem(TEXT_SCALE_KEY, textScale)
  }, [textScale])

  useEffect(() => {
    // The whole layout is still built RTL-first, so we don't flip `dir` yet —
    // only the language tag and the translated strings switch for now.
    document.documentElement.lang = language
    localStorage.setItem(LANGUAGE_KEY, language)
  }, [language])

  const value = useMemo<SettingsContextValue>(() => ({
    theme,
    setTheme: setThemeState,
    textScale,
    setTextScale: setTextScaleState,
    language,
    setLanguage: setLanguageState,
    t: (key: string) => translate(key, language),
  }), [theme, textScale, language])

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within a SettingsProvider')
  return ctx
}
