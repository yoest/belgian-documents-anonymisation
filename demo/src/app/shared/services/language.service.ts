import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { effect, inject, PLATFORM_ID, Service, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { TranslateService } from '@ngx-translate/core';

export const SUPPORTED_LANGUAGES = ['fr', 'en'] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

const DEFAULT_LANGUAGE: Language = 'fr';
const STORAGE_KEY = 'esty-language';

@Service()
export class LanguageService {
  private readonly translate = inject(TranslateService);
  private readonly document = inject(DOCUMENT);
  private readonly title = inject(Title);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  private readonly language = signal<Language>(this.initialLanguage());
  readonly current = this.language.asReadonly();

  constructor() {
    this.translate.setFallbackLang(DEFAULT_LANGUAGE);
    // Syncs the non-reactive translation library, <html lang>, <title> and the stored preference
    effect(() => {
      const language = this.language();
      this.translate.use(language);
      this.document.documentElement.lang = language;
      this.title.setTitle(this.translate.instant('app.title'));
      if (this.isBrowser) {
        safeStorage(() => localStorage.setItem(STORAGE_KEY, language));
      }
    });
  }

  use(language: Language): void {
    this.language.set(language);
  }

  private initialLanguage(): Language {
    if (!this.isBrowser) {
      return DEFAULT_LANGUAGE;
    }
    const stored = safeStorage(() => localStorage.getItem(STORAGE_KEY)) ?? null;
    if (isLanguage(stored)) {
      return stored;
    }
    const browserLanguage = navigator.language.slice(0, 2);
    return isLanguage(browserLanguage) ? browserLanguage : DEFAULT_LANGUAGE;
  }
}

// Storage can be blocked (private browsing, strict privacy settings): the preference is optional
function safeStorage<T>(access: () => T): T | undefined {
  try {
    return access();
  } catch {
    return undefined;
  }
}

function isLanguage(value: string | null): value is Language {
  return SUPPORTED_LANGUAGES.includes(value as Language);
}
