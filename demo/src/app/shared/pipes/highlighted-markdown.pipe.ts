import { Pipe, PipeTransform } from '@angular/core';
import { Marked } from 'marked';

import { DetectedEntity, EntityType } from '../models/anonymization.model';
import { EntitySegmentsPipe, SegmentSide } from './entity-segments.pipe';

const HTML_ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
};

function escapeHtml(value: string): string {
  return value.replace(/[&<>"]/g, (char) => HTML_ESCAPES[char]);
}

/**
 * Renders the document Markdown as HTML, with detected values (original side) or their
 * placeholders (anonymized side) wrapped in <mark>.
 *
 * The document text is HTML-escaped before rendering, so content coming from the PDF can never
 * inject markup; Angular's sanitizer still runs on the result when bound to [innerHTML].
 */
@Pipe({ name: 'highlightedMarkdown' })
export class HighlightedMarkdownPipe implements PipeTransform {
  private readonly segments = new EntitySegmentsPipe();
  private readonly marked = new Marked({
    gfm: true,
    async: false,
    // Links (including auto-linked emails and URLs) are shown as plain text: nothing to click
    // in a confidential document
    renderer: {
      link(token) {
        return this.parser.parseInline(token.tokens);
      },
    },
  });

  transform(
    markdown: string,
    entities: DetectedEntity[],
    side: SegmentSide,
    typeLabels: Partial<Record<EntityType, string>>,
  ): string {
    const markClass = side === 'anonymized' ? 'entity entity--placeholder' : 'entity';
    const source = this.segments
      .transform(markdown, entities, side)
      .map(({ text, entity }) => {
        if (!entity) {
          return escapeHtml(text);
        }
        const label = escapeHtml(typeLabels[entity.entityType] ?? entity.entityType);
        return `<mark class="${markClass}" title="${label}">${escapeHtml(text)}</mark>`;
      })
      .join('');
    return this.marked.parse(source, { async: false });
  }
}
