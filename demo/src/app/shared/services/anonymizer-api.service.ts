import { HttpClient, httpResource, HttpResourceRef } from '@angular/common/http';
import { inject, Service, Signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import {
  AnonymizationResult,
  DetectedEntity,
  EntityType,
  MappingEntry,
} from '../models/anonymization.model';

// Same-origin path, forwarded to the core API by the SSR server (see server.ts)
export const API_BASE_URL = '/api';

interface ApiEntity {
  placeholder: string;
  entity_type: EntityType;
  text: string;
  start: number;
  end: number;
  score: number;
}

interface ApiMappingEntry {
  placeholder: string;
  entity_type: EntityType;
  value: string;
  variants: string[];
}

interface ApiAnonymizeResponse {
  document_id: string;
  filename: string;
  page_count: number;
  processing_ms: number;
  original_text: string;
  anonymized_text: string;
  entities: ApiEntity[];
  mapping: ApiMappingEntry[];
}

@Service()
export class AnonymizerApiService {
  private readonly http = inject(HttpClient);

  /** Uploads the file whenever the signal holds one. Must be called in an injection context. */
  anonymize(file: Signal<File | undefined>): HttpResourceRef<AnonymizationResult | undefined> {
    return httpResource(
      () => {
        const selected = file();
        if (!selected) {
          return undefined;
        }
        const body = new FormData();
        body.append('file', selected, selected.name);
        return { url: `${API_BASE_URL}/anonymize`, method: 'POST', body };
      },
      { parse: (raw) => toAnonymizationResult(raw as ApiAnonymizeResponse) },
    );
  }

  /** Forgets the document and its mapping on the server. */
  async deleteDocument(documentId: string): Promise<void> {
    await firstValueFrom(this.http.delete<void>(this.documentUrl(documentId)));
  }

  /** Download link of the anonymised Markdown. */
  exportMarkdownUrl(documentId: string): string {
    return `${this.documentUrl(documentId)}/anonymized?download=true`;
  }

  /** PNG image of a page (0-based) of the original PDF, rendered by the core API. */
  originalPageUrl(documentId: string, pageNumber: number): string {
    return `${this.documentUrl(documentId)}/pages/${pageNumber}`;
  }

  private documentUrl(documentId: string): string {
    return `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`;
  }
}

function toAnonymizationResult(response: ApiAnonymizeResponse): AnonymizationResult {
  return {
    documentId: response.document_id,
    filename: response.filename,
    pageCount: response.page_count,
    processingMs: response.processing_ms,
    originalText: response.original_text,
    anonymizedText: response.anonymized_text,
    entities: response.entities.map((entity): DetectedEntity => ({
      placeholder: entity.placeholder,
      entityType: entity.entity_type,
      text: entity.text,
      start: entity.start,
      end: entity.end,
      score: entity.score,
    })),
    mapping: response.mapping.map((entry): MappingEntry => ({
      placeholder: entry.placeholder,
      entityType: entry.entity_type,
      value: entry.value,
      variants: entry.variants,
    })),
  };
}
