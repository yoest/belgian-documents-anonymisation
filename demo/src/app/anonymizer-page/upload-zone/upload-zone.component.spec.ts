import { ComponentFixture, TestBed } from '@angular/core/testing';

import { pdfFile, provideTestDefaults } from '../../../testing/test-providers';
import { UploadZoneComponent } from './upload-zone.component';

describe('UploadZoneComponent', () => {
  let fixture: ComponentFixture<UploadZoneComponent>;
  let selected: File[];

  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [UploadZoneComponent],
      providers: provideTestDefaults(),
    });
    fixture = TestBed.createComponent(UploadZoneComponent);
    fixture.componentRef.setInput('maxSizeMb', 1);
    selected = [];
    fixture.componentInstance.fileSelected.subscribe((file) => selected.push(file));
    await fixture.whenStable();
  });

  function choose(file: File): void {
    const input = fixture.nativeElement.querySelector('input[type=file]') as HTMLInputElement;
    Object.defineProperty(input, 'files', { value: { item: () => file }, configurable: true });
    input.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  function alertText(): string | undefined {
    return (fixture.nativeElement as HTMLElement)
      .querySelector('[role=alert]')
      ?.textContent?.trim();
  }

  it('emits a valid PDF', () => {
    const file = pdfFile();
    choose(file);
    expect(selected).toEqual([file]);
    expect(alertText()).toBeUndefined();
  });

  it('rejects other file types', () => {
    choose(new File(['x'], 'notes.docx', { type: 'application/msword' }));
    expect(selected).toEqual([]);
    expect(alertText()).toBe('Only PDF files are supported.');
  });

  it('rejects files above the size limit', () => {
    choose(pdfFile('big.pdf', 2 * 1024 * 1024));
    expect(selected).toEqual([]);
    expect(alertText()).toBe('This file exceeds 1 MB.');
  });

  it('accepts a dropped file', () => {
    const file = pdfFile();
    const drop = new Event('drop') as DragEvent;
    Object.defineProperty(drop, 'dataTransfer', { value: { files: { item: () => file } } });
    fixture.nativeElement.dispatchEvent(drop);
    expect(selected).toEqual([file]);
  });
});
