import { Pipe, PipeTransform } from '@angular/core';

import { DetectedEntity } from '../models/anonymization.model';

export interface TextSegment {
  text: string;
  /** Set when the segment is a detected value (original side) or its placeholder (anonymized side). */
  entity?: DetectedEntity;
}

export type SegmentSide = 'original' | 'anonymized';

/** Splits the original text into plain parts and detected values, or their placeholders. */
@Pipe({ name: 'entitySegments' })
export class EntitySegmentsPipe implements PipeTransform {
  transform(originalText: string, entities: DetectedEntity[], side: SegmentSide): TextSegment[] {
    const segments: TextSegment[] = [];
    let cursor = 0;
    for (const entity of [...entities].sort((a, b) => a.start - b.start)) {
      if (entity.start < cursor) {
        continue;
      }
      if (entity.start > cursor) {
        segments.push({ text: originalText.slice(cursor, entity.start) });
      }
      segments.push({ text: side === 'original' ? entity.text : entity.placeholder, entity });
      cursor = entity.end;
    }
    if (cursor < originalText.length) {
      segments.push({ text: originalText.slice(cursor) });
    }
    return segments;
  }
}
