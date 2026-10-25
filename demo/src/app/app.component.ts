import { NgOptimizedImage } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { LanguageSwitchComponent } from './shared/components/language-switch/language-switch.component';
import { LanguageService } from './shared/services/language.service';

@Component({
  selector: 'esty-root',
  imports: [LanguageSwitchComponent, NgOptimizedImage, RouterOutlet, TranslatePipe],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  // Instantiated here so the language is applied before the first render
  protected readonly language = inject(LanguageService);
}
