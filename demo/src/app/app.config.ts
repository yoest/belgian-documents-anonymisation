import { provideHttpClient, withFetch } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideTranslateLoader, provideTranslateService } from '@ngx-translate/core';

import { routes } from './app.routes';
import { StaticTranslateLoader } from './shared/i18n/static-translate.loader';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideClientHydration(withEventReplay()),
    provideHttpClient(withFetch()),
    provideTranslateService({
      loader: provideTranslateLoader(() => new StaticTranslateLoader()),
      fallbackLang: 'fr',
      lang: 'fr',
    }),
  ],
};
