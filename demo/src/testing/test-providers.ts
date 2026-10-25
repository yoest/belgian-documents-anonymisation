import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { EnvironmentProviders, Provider } from '@angular/core';
import { provideTranslateLoader, provideTranslateService } from '@ngx-translate/core';

import { StaticTranslateLoader } from '../app/shared/i18n/static-translate.loader';

/** Real English translations and a mocked HTTP backend, shared by component and service specs. */
export function provideTestDefaults(): (Provider | EnvironmentProviders)[] {
  return [
    provideHttpClient(),
    provideHttpClientTesting(),
    provideTranslateService({
      loader: provideTranslateLoader(() => new StaticTranslateLoader()),
      fallbackLang: 'en',
      lang: 'en',
    }),
  ];
}

export const API_ANONYMIZE_RESPONSE = {
  document_id: 'doc-1',
  filename: 'bail.pdf',
  page_count: 2,
  processing_ms: 1500,
  original_text: 'Monsieur Jan Peeters, IBAN BE68 5390 0754 7034. Signé Jan Peeters.',
  anonymized_text: 'Monsieur [PERSON_1], IBAN [IBAN_1]. Signé [PERSON_1].',
  entities: [
    {
      placeholder: '[PERSON_1]',
      entity_type: 'PERSON',
      text: 'Jan Peeters',
      start: 9,
      end: 20,
      score: 0.9,
      source: 'ner',
    },
    {
      placeholder: '[IBAN_1]',
      entity_type: 'IBAN',
      text: 'BE68 5390 0754 7034',
      start: 27,
      end: 46,
      score: 0.99,
      source: 'regex',
    },
    {
      placeholder: '[PERSON_1]',
      entity_type: 'PERSON',
      text: 'Jan Peeters',
      start: 54,
      end: 65,
      score: 0.8,
      source: 'propagation',
    },
  ],
  mapping: [
    {
      placeholder: '[PERSON_1]',
      entity_type: 'PERSON',
      value: 'Jan Peeters',
      variants: ['Jan Peeters'],
    },
    {
      placeholder: '[IBAN_1]',
      entity_type: 'IBAN',
      value: 'BE68 5390 0754 7034',
      variants: ['BE68 5390 0754 7034'],
    },
  ],
};

export function pdfFile(name = 'bail.pdf', sizeBytes = 1024): File {
  return new File([new Uint8Array(sizeBytes)], name, { type: 'application/pdf' });
}
