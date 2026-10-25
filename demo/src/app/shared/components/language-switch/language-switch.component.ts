import { UpperCasePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

import { LanguageService, SUPPORTED_LANGUAGES } from '../../services/language.service';

@Component({
  selector: 'esty-language-switch',
  imports: [TranslatePipe, UpperCasePipe],
  templateUrl: './language-switch.component.html',
  styleUrl: './language-switch.component.scss',
})
export class LanguageSwitchComponent {
  protected readonly languageService = inject(LanguageService);
  protected readonly languages = SUPPORTED_LANGUAGES;
}
