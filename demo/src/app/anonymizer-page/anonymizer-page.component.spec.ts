import { HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { API_ANONYMIZE_RESPONSE, pdfFile, provideTestDefaults } from '../../testing/test-providers';
import { AnonymizerPageComponent } from './anonymizer-page.component';
import { UploadZoneComponent } from './upload-zone/upload-zone.component';

describe('AnonymizerPageComponent', () => {
  let fixture: ComponentFixture<AnonymizerPageComponent>;
  let http: HttpTestingController;
  let element: HTMLElement;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [AnonymizerPageComponent],
      providers: provideTestDefaults(),
    });
    fixture = TestBed.createComponent(AnonymizerPageComponent);
    http = TestBed.inject(HttpTestingController);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  afterEach(() => http.verify());

  async function upload(): Promise<void> {
    const uploadZone = fixture.debugElement.query(
      (node) => node.componentInstance instanceof UploadZoneComponent,
    );
    (uploadZone.componentInstance as UploadZoneComponent).fileSelected.emit(pdfFile());
    fixture.detectChanges();
    TestBed.tick();
  }

  function button(label: string): HTMLButtonElement {
    const found = [...element.querySelectorAll('button')].find(
      (b) => b.textContent?.trim() === label,
    );
    if (!found) {
      throw new Error(`No button "${label}"`);
    }
    return found;
  }

  it('shows the progress, then the original PDF pages next to the anonymized document', async () => {
    await upload();
    expect(element.querySelector('[role=status]')?.textContent).toContain('Anonymizing bail.pdf');

    http.expectOne('/api/anonymize').flush(API_ANONYMIZE_RESPONSE);
    await fixture.whenStable();

    expect(element.querySelector('h2')?.textContent).toBe('bail.pdf');
    expect(element.textContent).toContain('2 page(s) · 2 values replaced · 1.5 s');
    const pages = [...element.querySelectorAll('img')];
    expect(pages.map((page) => page.getAttribute('src'))).toEqual([
      '/api/documents/doc-1/pages/0',
      '/api/documents/doc-1/pages/1',
    ]);
    expect(pages[1].alt).toBe('Page 2 of 2');
    const marks = [...element.querySelectorAll('mark')].map((mark) => mark.textContent);
    expect(marks).toEqual(['[PERSON_1]', '[IBAN_1]', '[PERSON_1]']);
    const panes = [...element.querySelectorAll('[role=region]')].map((pane) =>
      pane.textContent?.trim(),
    );
    expect(panes[1]).toBe(API_ANONYMIZE_RESPONSE.anonymized_text);
  });

  it('switches the original to Markdown with the detected values highlighted', async () => {
    await upload();
    http.expectOne('/api/anonymize').flush(API_ANONYMIZE_RESPONSE);
    await fixture.whenStable();

    const markdown = button('Markdown');
    markdown.click();
    await fixture.whenStable();

    expect(markdown.getAttribute('aria-pressed')).toBe('true');
    expect(element.querySelector('img')).toBeNull();
    const marks = [...element.querySelectorAll('mark')].map((mark) => mark.textContent);
    expect(marks).toEqual([
      'Jan Peeters',
      'BE68 5390 0754 7034',
      'Jan Peeters',
      '[PERSON_1]',
      '[IBAN_1]',
      '[PERSON_1]',
    ]);
  });

  it('exports the anonymized Markdown only', async () => {
    await upload();
    http.expectOne('/api/anonymize').flush(API_ANONYMIZE_RESPONSE);
    await fixture.whenStable();

    const links = [...element.querySelectorAll('a')];
    expect(links.map((link) => link.textContent?.trim())).toEqual(['Export Markdown']);
    expect(links[0].getAttribute('href')).toBe('/api/documents/doc-1/anonymized?download=true');
  });

  it('explains an unsupported PDF', async () => {
    await upload();
    http
      .expectOne('/api/anonymize')
      .flush(
        { detail: 'The PDF has no text layer.' },
        { status: 422, statusText: 'Unprocessable' },
      );
    await fixture.whenStable();

    expect(element.querySelector('[role=alert]')?.textContent).toContain(
      'Scanned or password-protected',
    );
  });

  it('forgets the document on "New document"', async () => {
    await upload();
    http.expectOne('/api/anonymize').flush(API_ANONYMIZE_RESPONSE);
    await fixture.whenStable();

    button('New document').click();
    http.expectOne({ method: 'DELETE', url: '/api/documents/doc-1' }).flush(null);
    await fixture.whenStable();
    expect(element.querySelector('esty-upload-zone')).not.toBeNull();
  });
});
