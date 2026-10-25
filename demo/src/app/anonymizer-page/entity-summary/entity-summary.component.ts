import { Component, computed, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

import { DetectedEntity, EntityType } from '../../shared/models/anonymization.model';

interface EntityCount {
  type: EntityType;
  /** Distinct values (placeholders), not occurrences: "Jan Peeters" counts once. */
  count: number;
}

@Component({
  selector: 'esty-entity-summary',
  imports: [TranslatePipe],
  templateUrl: './entity-summary.component.html',
  styleUrl: './entity-summary.component.scss',
})
export class EntitySummaryComponent {
  readonly entities = input.required<DetectedEntity[]>();

  protected readonly counts = computed<EntityCount[]>(() => {
    const placeholders = new Map<EntityType, Set<string>>();
    for (const entity of this.entities()) {
      const values = placeholders.get(entity.entityType) ?? new Set<string>();
      values.add(entity.placeholder);
      placeholders.set(entity.entityType, values);
    }
    return [...placeholders]
      .map(([type, values]) => ({ type, count: values.size }))
      .sort((a, b) => b.count - a.count || a.type.localeCompare(b.type));
  });
}
