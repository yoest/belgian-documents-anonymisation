import { DetectedEntity } from '../models/anonymization.model';
import { EntitySegmentsPipe } from './entity-segments.pipe';

const TEXT = 'Monsieur Jan Peeters, IBAN BE68.';
const ENTITIES: DetectedEntity[] = [
  { placeholder: '[IBAN_1]', entityType: 'IBAN', text: 'BE68', start: 27, end: 31, score: 1 },
  {
    placeholder: '[PERSON_1]',
    entityType: 'PERSON',
    text: 'Jan Peeters',
    start: 9,
    end: 20,
    score: 1,
  },
];

describe('EntitySegmentsPipe', () => {
  const pipe = new EntitySegmentsPipe();

  it('splits the original text around detected values, in text order', () => {
    const segments = pipe.transform(TEXT, ENTITIES, 'original');
    expect(segments.map((segment) => segment.text)).toEqual([
      'Monsieur ',
      'Jan Peeters',
      ', IBAN ',
      'BE68',
      '.',
    ]);
    expect(segments[1].entity?.entityType).toBe('PERSON');
  });

  it('shows placeholders on the anonymized side', () => {
    const text = pipe
      .transform(TEXT, ENTITIES, 'anonymized')
      .map((segment) => segment.text)
      .join('');
    expect(text).toBe('Monsieur [PERSON_1], IBAN [IBAN_1].');
  });

  it('returns the whole text when nothing was detected', () => {
    expect(pipe.transform(TEXT, [], 'original')).toEqual([{ text: TEXT }]);
  });
});
