import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./anonymizer-page/anonymizer-page.component').then((m) => m.AnonymizerPageComponent),
  },
  { path: '**', redirectTo: '' },
];
