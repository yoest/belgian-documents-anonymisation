import { TranslateLoader, TranslationObject } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';

import en from '../../../assets/i18n/en.json';
import fr from '../../../assets/i18n/fr.json';

const TRANSLATIONS: Record<string, TranslationObject> = { en, fr };

/**
 * Translations are bundled rather than fetched over HTTP: identical behaviour in the browser,
 * during SSR/prerendering and in tests, with no extra request or flash of untranslated keys.
 */
export class StaticTranslateLoader implements TranslateLoader {
  getTranslation(lang: string): Observable<TranslationObject> {
    return of(TRANSLATIONS[lang] ?? TRANSLATIONS['en']);
  }
}
