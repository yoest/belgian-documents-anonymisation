import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { provideTestDefaults } from '../testing/test-providers';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [provideTestDefaults(), provideRouter([])],
    });
  });

  it('switches the language of the interface and of the document', async () => {
    const fixture = TestBed.createComponent(AppComponent);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;

    const french = [...element.querySelectorAll('button')].find(
      (button) => button.textContent?.trim() === 'FR',
    );
    french?.click();
    await fixture.whenStable();

    expect(element.querySelector('h1')?.textContent).toBe('Anonymiseur de documents belges');
    expect(french?.getAttribute('aria-pressed')).toBe('true');
    expect(document.documentElement.lang).toBe('fr');
    expect(document.title).toBe('Anonymiseur de documents belges');
  });

  it('credits Estytech with a link opening in a new tab', async () => {
    const fixture = TestBed.createComponent(AppComponent);
    await fixture.whenStable();
    const link = (fixture.nativeElement as HTMLElement).querySelector('footer a');
    expect(link?.getAttribute('href')).toBe('https://estytech.com');
    expect(link?.getAttribute('target')).toBe('_blank');
    expect(link?.getAttribute('rel')).toBe('noopener');
  });
});
