export type EntityType =
  | 'ADDRESS'
  | 'DATE_OF_BIRTH'
  | 'EMAIL'
  | 'ENTERPRISE_NUMBER'
  | 'IBAN'
  | 'ID_CARD_NUMBER'
  | 'LICENSE_PLATE'
  | 'NATIONAL_NUMBER'
  | 'ORGANIZATION'
  | 'PERSON'
  | 'PHONE';

export interface DetectedEntity {
  placeholder: string;
  entityType: EntityType;
  text: string;
  /** Offsets in the original text, end exclusive. */
  start: number;
  end: number;
  score: number;
}

export interface MappingEntry {
  placeholder: string;
  entityType: EntityType;
  value: string;
  variants: string[];
}

export interface AnonymizationResult {
  documentId: string;
  filename: string;
  pageCount: number;
  processingMs: number;
  originalText: string;
  anonymizedText: string;
  entities: DetectedEntity[];
  mapping: MappingEntry[];
}
