import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

import { AnonymizerApiService } from '../shared/services/anonymizer-api.service';
import { DocumentComparisonComponent } from './document-comparison/document-comparison.component';
import { EntitySummaryComponent } from './entity-summary/entity-summary.component';
import { UploadZoneComponent } from './upload-zone/upload-zone.component';

// Must match api.max_upload_size_mb in the core configuration
const MAX_UPLOAD_SIZE_MB = 20;

@Component({
  selector: 'esty-anonymizer-page',
  host: {
    '[class.page--centered]': '!result()',
  },
  imports: [
    DocumentComparisonComponent,
    EntitySummaryComponent,
    TranslatePipe,
    UploadZoneComponent,
  ],
  templateUrl: './anonymizer-page.component.html',
  styleUrl: './anonymizer-page.component.scss',
})
export class AnonymizerPageComponent {
  private readonly api = inject(AnonymizerApiService);

  protected readonly maxUploadSizeMb = MAX_UPLOAD_SIZE_MB;

  // No resource id on purpose: results are private to the user and must never be cached by SSR
  protected readonly file = signal<File | undefined>(undefined);
  protected readonly anonymization = this.api.anonymize(this.file);
  protected readonly result = computed(() =>
    this.anonymization.hasValue() ? this.anonymization.value() : undefined,
  );
  protected readonly errorKey = computed(() => {
    const error = this.anonymization.error();
    if (!error) {
      return null;
    }
    const status = error instanceof HttpErrorResponse ? error.status : 0;
    // The SSR proxy answers 502/504 when the core API cannot be reached
    const keys: Record<number, string> = {
      413: 'errors.tooLarge',
      422: 'errors.invalidPdf',
      502: 'errors.unavailable',
      504: 'errors.unavailable',
    };
    return keys[status] ?? 'errors.generic';
  });

  protected readonly stats = computed(() => {
    const result = this.result();
    return result
      ? {
          pages: result.pageCount,
          entities: new Set(result.entities.map((entity) => entity.placeholder)).size,
          seconds: (result.processingMs / 1000).toFixed(1),
        }
      : undefined;
  });
  protected readonly exportMarkdownUrl = computed(() => {
    const result = this.result();
    return result ? this.api.exportMarkdownUrl(result.documentId) : undefined;
  });

  protected readonly originalPageUrls = computed(() => {
    const result = this.result();
    return result
      ? Array.from({ length: result.pageCount }, (_, page) =>
          this.api.originalPageUrl(result.documentId, page),
        )
      : [];
  });

  protected onFileSelected(file: File): void {
    this.file.set(file);
  }

  protected async startOver(): Promise<void> {
    const documentId = this.result()?.documentId;
    this.file.set(undefined);
    if (documentId) {
      // The document and its mapping are dropped server-side; it expires anyway if this fails
      await this.api.deleteDocument(documentId).catch(() => undefined);
    }
  }
}
