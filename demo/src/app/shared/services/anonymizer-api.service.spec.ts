import { HttpTestingController } from '@angular/common/http/testing';
import { ApplicationRef, Injector, runInInjectionContext, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import {
  API_ANONYMIZE_RESPONSE,
  pdfFile,
  provideTestDefaults,
} from '../../../testing/test-providers';
import { AnonymizerApiService } from './anonymizer-api.service';

describe('AnonymizerApiService', () => {
  let service: AnonymizerApiService;
  let http: HttpTestingController;
  let injector: Injector;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: provideTestDefaults() });
    service = TestBed.inject(AnonymizerApiService);
    http = TestBed.inject(HttpTestingController);
    injector = TestBed.inject(Injector);
  });

  afterEach(() => http.verify());

  it('stays idle until a file is selected, then uploads it and maps the response', async () => {
    const file = signal<File | undefined>(undefined);
    const resource = runInInjectionContext(injector, () => service.anonymize(file));
    TestBed.tick();
    http.expectNone('/api/anonymize');

    file.set(pdfFile());
    TestBed.tick();
    const request = http.expectOne('/api/anonymize');
    expect(request.request.method).toBe('POST');
    expect((request.request.body as FormData).get('file')).toBeInstanceOf(File);
    request.flush(API_ANONYMIZE_RESPONSE);
    await TestBed.inject(ApplicationRef).whenStable();

    const result = resource.value();
    expect(result?.documentId).toBe('doc-1');
    expect(result?.entities[1]).toEqual(
      expect.objectContaining({ entityType: 'IBAN', placeholder: '[IBAN_1]', start: 27, end: 46 }),
    );
    expect(result?.mapping[0].value).toBe('Jan Peeters');
  });

  it('deletes a document', async () => {
    const deletion = service.deleteDocument('doc-1');
    http.expectOne({ method: 'DELETE', url: '/api/documents/doc-1' }).flush(null);
    await expect(deletion).resolves.toBeUndefined();
  });

  it('builds the original page URLs', () => {
    expect(service.originalPageUrl('doc 1', 2)).toBe('/api/documents/doc%201/pages/2');
  });

  it('builds the Markdown export URL', () => {
    expect(service.exportMarkdownUrl('doc 1')).toBe(
      '/api/documents/doc%201/anonymized?download=true',
    );
  });
});
