// Copyright (c) 2026 PotterWhite — MIT License

/**
 * i18n setup for SynapseERP.
 *
 * Design principles (low-coupling, easy to extend):
 *   - Each language is a plain TypeScript object in src/locales/<lang>.ts
 *   - The active locale is persisted in localStorage under LOCALE_KEY
 *   - To add a new language:
 *       1. Create src/locales/<lang>.ts with the same key structure
 *       2. Import it here and add to the `messages` map
 *       3. Add a langOption entry in Header.vue
 *   - vue-i18n v9 composition API (useI18n) is used throughout
 */

import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN'
import enUS from '@/locales/en-US'

export const LOCALE_KEY = 'synapse_locale'
export const SUPPORTED_LOCALES = ['zh-CN', 'en-US'] as const
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

function getInitialLocale(): SupportedLocale {
  const stored = localStorage.getItem(LOCALE_KEY)
  if (stored && (SUPPORTED_LOCALES as readonly string[]).includes(stored)) {
    return stored as SupportedLocale
  }
  // Default: Chinese
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false,           // Use Composition API mode
  locale: getInitialLocale(),
  fallbackLocale: 'en-US',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

/** Switch locale and persist to localStorage */
export function setLocale(locale: SupportedLocale) {
  ;(i18n.global.locale as { value: string }).value = locale
  localStorage.setItem(LOCALE_KEY, locale)
  document.documentElement.lang = locale
}

export default i18n
