import { Component, inject, input, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { map } from 'rxjs';

import { DetectedEntity, EntityType } from '../../shared/models/anonymization.model';
import { HighlightedMarkdownPipe } from '../../shared/pipes/highlighted-markdown.pipe';

export type OriginalView = 'pdf' | 'markdown';

@Component({
  selector: 'esty-document-comparison',
  imports: [HighlightedMarkdownPipe, TranslatePipe],
  templateUrl: './document-comparison.component.html',
  styleUrl: './document-comparison.component.scss',
})
export class DocumentComparisonComponent {
  readonly markdown = input.required<string>();
  readonly entities = input.required<DetectedEntity[]>();
  readonly originalPageUrls = input.required<string[]>();

  // The original is shown as the real PDF by default; Markdown shows what the detection worked on
  protected readonly originalView = signal<OriginalView>('pdf');
  protected readonly originalViews: OriginalView[] = ['pdf', 'markdown'];

  // Tooltips of the highlighted values, in the current language
  protected readonly typeLabels = toSignal(
    inject(TranslateService)
      .stream('entityTypes')
      .pipe(map((labels) => labels as Partial<Record<EntityType, string>>)),
    { initialValue: {} },
  );
}
