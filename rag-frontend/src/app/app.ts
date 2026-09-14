import { Component, signal } from '@angular/core';
import { PdfQa } from './components/pdf-qa/pdf-qa';
import { CodeExplainer } from './components/code-explainer/code-explainer';
import { AuthService } from './services/auth';

type Onglet = 'pdf' | 'code';

@Component({
  selector: 'app-root',
  imports: [PdfQa, CodeExplainer],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('rag-frontend');
  ongletActif = signal<Onglet>('pdf');

  constructor(protected authService: AuthService) {}

  changerOnglet(onglet: Onglet) {
    this.ongletActif.set(onglet);
  }

  seConnecter() {
    this.authService.login();
  }

  seDeconnecter() {
    this.authService.logout();
  }
}