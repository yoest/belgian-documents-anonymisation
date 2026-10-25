import { Component, computed, input, output, signal } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

const BYTES_PER_MB = 1024 * 1024;

type ValidationError = 'invalidType' | 'tooLarge';

@Component({
  selector: 'esty-upload-zone',
  imports: [TranslatePipe],
  templateUrl: './upload-zone.component.html',
  styleUrl: './upload-zone.component.scss',
  host: {
    '[class.upload-zone--dragging]': 'dragging()',
    '(dragover)': 'onDragOver($event)',
    '(dragleave)': 'dragging.set(false)',
    '(drop)': 'onDrop($event)',
  },
})
export class UploadZoneComponent {
  readonly maxSizeMb = input(20);
  readonly fileSelected = output<File>();

  protected readonly dragging = signal(false);
  protected readonly error = signal<ValidationError | null>(null);
  protected readonly errorParams = computed(() => ({ max: this.maxSizeMb() }));

  protected onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.item(0);
    // Reset so that choosing the same file again still triggers a change event
    input.value = '';
    if (file) {
      this.select(file);
    }
  }

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(true);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(false);
    const file = event.dataTransfer?.files.item(0);
    if (file) {
      this.select(file);
    }
  }

  private select(file: File): void {
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      this.error.set('invalidType');
    } else if (file.size > this.maxSizeMb() * BYTES_PER_MB) {
      this.error.set('tooLarge');
    } else {
      this.error.set(null);
      this.fileSelected.emit(file);
    }
  }
}
