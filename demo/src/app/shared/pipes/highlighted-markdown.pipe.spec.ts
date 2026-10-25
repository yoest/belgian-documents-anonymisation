import { DetectedEntity } from '../models/anonymization.model';
import { HighlightedMarkdownPipe } from './highlighted-markdown.pipe';

const LABELS = { PERSON: 'Person', IBAN: 'Bank account' };

function at(markdown: string, text: string, entity: Partial<DetectedEntity>): DetectedEntity {
  const start = markdown.indexOf(text);
  return {
    placeholder: '',
    entityType: 'PERSON',
    text,
    start,
    end: start + text.length,
    score: 1,
    ...entity,
  };
}

function render(
  markdown: string,
  entities: DetectedEntity[],
  side: 'original' | 'anonymized',
): HTMLElement {
  const container = document.createElement('div');
  container.innerHTML = new HighlightedMarkdownPipe().transform(markdown, entities, side, LABELS);
  return container;
}

describe('HighlightedMarkdownPipe', () => {
  const markdown = [
    '## Article 3 - Loyer',
    '',
    'Payé par Jan Peeters :',
    '',
    '| Échéance | Compte |',
    '|---|---|',
    '| 1er septembre | BE68 5390 0754 7034 |',
  ].join('\n');
  const entities = [
    at(markdown, 'Jan Peeters', { placeholder: '[PERSON_1]', entityType: 'PERSON' }),
    at(markdown, 'BE68 5390 0754 7034', { placeholder: '[IBAN_1]', entityType: 'IBAN' }),
  ];

  it('renders headings, paragraphs and tables with highlighted values', () => {
    const html = render(markdown, entities, 'original');
    expect(html.querySelector('h2')?.textContent).toBe('Article 3 - Loyer');
    expect(html.querySelector('td:last-child')?.textContent).toBe('BE68 5390 0754 7034');
    const marks = [...html.querySelectorAll('mark')];
    expect(marks.map((mark) => mark.textContent)).toEqual(['Jan Peeters', 'BE68 5390 0754 7034']);
    expect(marks[1].title).toBe('Bank account');
  });

  it('shows placeholders on the anonymized side', () => {
    const marks = [...render(markdown, entities, 'anonymized').querySelectorAll('mark')];
    expect(marks.map((mark) => mark.textContent)).toEqual(['[PERSON_1]', '[IBAN_1]']);
    expect(marks[0].classList).toContain('entity--placeholder');
  });

  it('renders links and e-mail addresses as plain text', () => {
    const html = render('Contact: jan@example.be or [site](https://example.be)', [], 'original');
    expect(html.querySelector('a')).toBeNull();
    expect(html.textContent?.trim()).toBe('Contact: jan@example.be or site');
  });

  it('never interprets the document text as HTML', () => {
    const hostile = 'Clause <img src=x onerror="alert(1)"> & <script>alert(2)</script>';
    const html = render(hostile, [], 'original');
    expect(html.querySelector('img, script')).toBeNull();
    expect(html.textContent).toContain('<img src=x onerror="alert(1)"> & <script>');
  });
});
