import { Component, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CodeExplainerService, AnalyzeResponse } from '../../services/code-explainer';

interface EntreeHistorique {
  url: string;
  resultat: AnalyzeResponse;
  date: string; // date lisible, ex: "21/08/2026 14:32"
}

type HistoriqueParUrl = Record<string, EntreeHistorique>;

const CLE_STOCKAGE = 'rag-code-explainer-historique';

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

  historique = signal<HistoriqueParUrl>(this.chargerHistorique());

  constructor(private codeExplainerService: CodeExplainerService) {
    effect(() => {
      const historiqueActuel = this.historique();
      localStorage.setItem(CLE_STOCKAGE, JSON.stringify(historiqueActuel));
    });
  }

  private chargerHistorique(): HistoriqueParUrl {
    try {
      const donnees = localStorage.getItem(CLE_STOCKAGE);
      return donnees ? JSON.parse(donnees) : {};
    } catch {
      return {};
    }
  }

  /** Extrait un nom court et lisible depuis une URL GitHub, pour l'affichage des chips. */
  nomDepuisUrl(url: string): string {
    const morceaux = url.replace(/\/$/, '').split('/');
    return morceaux.slice(-2).join('/'); // ex: "utilisateur/nom-du-repo"
  }

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

        const maintenant = new Date().toLocaleString('fr-FR', {
          day: '2-digit', month: '2-digit', year: 'numeric',
          hour: '2-digit', minute: '2-digit'
        });

        this.historique.update(h => ({
          ...h,
          [url]: { url, resultat: res, date: maintenant }
        }));
      },
      error: (err) => {
        this.chargement.set(false);
        const detail = err?.error?.detail || "Impossible d'analyser ce repo. Vérifie l'URL et que les services tournent.";
        this.erreur.set(detail);
      }
    });
  }

  /** Recharge un résultat déjà en cache, sans refaire d'appel réseau. */
  chargerDepuisHistorique(entree: EntreeHistorique) {
    this.githubUrl = entree.url;
    this.resultat.set(entree.resultat);
    this.erreur.set(null);
  }

  supprimerDeLHistorique(url: string, event: Event) {
    event.stopPropagation();
    this.historique.update(h => {
      const copie = { ...h };
      delete copie[url];
      return copie;
    });
  }

  effacerTouLHistorique() {
    const confirmation = confirm("Effacer tout l'historique des repos analysés ? Cette action est irréversible.");
    if (confirmation) {
      this.historique.set({});
    }
  }

  get entreesHistorique(): EntreeHistorique[] {
    return Object.values(this.historique()).sort((a, b) => b.date.localeCompare(a.date));
  }
}