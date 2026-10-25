import { TestBed } from '@angular/core/testing';

import { provideTestDefaults } from '../../../testing/test-providers';
import { DetectedEntity } from '../../shared/models/anonymization.model';
import { EntitySummaryComponent } from './entity-summary.component';

function entity(placeholder: string, entityType: DetectedEntity['entityType']): DetectedEntity {
  return { placeholder, entityType, text: '', start: 0, end: 0, score: 1 };
}

describe('EntitySummaryComponent', () => {
  it('counts distinct values per type, most frequent first', async () => {
    TestBed.configureTestingModule({
      imports: [EntitySummaryComponent],
      providers: provideTestDefaults(),
    });
    const fixture = TestBed.createComponent(EntitySummaryComponent);
    fixture.componentRef.setInput('entities', [
      entity('[IBAN_1]', 'IBAN'),
      entity('[PERSON_1]', 'PERSON'),
      entity('[PERSON_1]', 'PERSON'),
      entity('[PERSON_2]', 'PERSON'),
    ]);
    await fixture.whenStable();

    const items = [...(fixture.nativeElement as HTMLElement).querySelectorAll('li')].map((item) =>
      item.textContent?.replace(/\s+/g, ' ').trim(),
    );
    expect(items).toEqual(['2 Person', '1 Bank account']);
  });
});
