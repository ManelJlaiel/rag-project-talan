import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CodeExplainerService, AnalyzeResponse } from '../../services/code-explainer';

@Component({
  selector: 'app-code-explainer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './code-explainer.html',
  styleUrl: './code-explainer.css'
})
export class CodeExplainer {
  githubUrl = '';
  resultat = signal<AnalyzeResponse | null>(null);
  chargement = signal(false);
  erreur = signal<string | null>(null);

  constructor(private codeExplainerService: CodeExplainerService) {}

  analyser() {
    const url = this.githubUrl.trim();
    if (!url || this.chargement()) return;

    this.chargement.set(true);
    this.erreur.set(null);
    this.resultat.set(null);

    this.codeExplainerService.analyzeRepo(url).subscribe({
      next: (res) => {
        this.resultat.set(res);
        this.chargement.set(false);
      },
      error: (err) => {
        this.chargement.set(false);
        const detail = err?.error?.detail || "Impossible d'analyser ce repo. Vérifie l'URL et que les services tournent.";
        this.erreur.set(detail);
      }
    });
  }
}