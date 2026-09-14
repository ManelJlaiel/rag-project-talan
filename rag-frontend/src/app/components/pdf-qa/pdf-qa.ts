import { Component, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PdfService } from '../../services/pdf';
import { AuthService } from '../../services/auth';

interface MessageChat {
  role: 'user' | 'assistant';
  texte: string;
  extraits?: string[];
}

type HistoriquesParDocument = Record<string, MessageChat[]>;

const CLE_STOCKAGE = 'rag-pdf-historiques-par-document';
const CLE_TOUS_DOCUMENTS = '__TOUS_LES_DOCUMENTS__';

@Component({
  selector: 'app-pdf-qa',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pdf-qa.html',
  styleUrl: './pdf-qa.css'
})
export class PdfQa {
  documents = signal<string[]>([]);
  documentSelectionne = signal<string | null>(null);
  question = '';

  historiques = signal<HistoriquesParDocument>(this.chargerHistoriques());

  private cleActuelle = computed(() => this.documentSelectionne() ?? CLE_TOUS_DOCUMENTS);
  messages = computed(() => this.historiques()[this.cleActuelle()] ?? []);

  fichierEnCours = signal(false);
  questionEnCours = signal(false);
  erreur = signal<string | null>(null);

  constructor(
    private pdfService: PdfService,
    protected authService: AuthService
  ) {
    this.chargerDocuments();

    effect(() => {
      const historiquesActuels = this.historiques();
      localStorage.setItem(CLE_STOCKAGE, JSON.stringify(historiquesActuels));
    });
  }

  private chargerHistoriques(): HistoriquesParDocument {
    try {
      const donnees = localStorage.getItem(CLE_STOCKAGE);
      return donnees ? JSON.parse(donnees) : {};
    } catch {
      return {};
    }
  }

  private ajouterMessage(message: MessageChat) {
    const cle = this.cleActuelle();
    this.historiques.update(historiques => ({
      ...historiques,
      [cle]: [...(historiques[cle] ?? []), message]
    }));
  }

  effacerHistoriqueActuel() {
    const nomAffiche = this.documentSelectionne() ?? 'tous les documents';
    const confirmation = confirm(`Effacer l'historique de conversation pour "${nomAffiche}" ? Cette action est irréversible.`);
    if (confirmation) {
      const cle = this.cleActuelle();
      this.historiques.update(historiques => {
        const copie = { ...historiques };
        delete copie[cle];
        return copie;
      });
    }
  }

  supprimerDocument(nomDocument: string, event: Event) {
    event.stopPropagation();

    const confirmation = confirm(`Supprimer "${nomDocument}" ? Il sera retiré de l'index et son historique de conversation sera perdu.`);
    if (!confirmation) return;

    this.pdfService.deleteDocument(nomDocument).subscribe({
      next: () => {
        if (this.documentSelectionne() === nomDocument) {
          this.documentSelectionne.set(null);
        }
        this.historiques.update(historiques => {
          const copie = { ...historiques };
          delete copie[nomDocument];
          return copie;
        });
        this.chargerDocuments();
      },
      error: () => {
        this.erreur.set(`Échec de la suppression de "${nomDocument}".`);
      }
    });
  }

  chargerDocuments() {
    this.pdfService.getDocuments().subscribe({
      next: (res) => this.documents.set(res.documents),
      error: () => this.erreur.set("Impossible de contacter le service PDF. Vérifie que la Gateway et le microservice tournent.")
    });
  }

  onFichierSelectionne(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const fichier = input.files[0];
    this.fichierEnCours.set(true);
    this.erreur.set(null);

    this.pdfService.uploadPdf(fichier).subscribe({
  next: () => {
    this.fichierEnCours.set(false);
    this.chargerDocuments();
    input.value = '';
  },
  error: (err) => {
    this.fichierEnCours.set(false);
    const detail = err?.error?.detail || "Échec de l'upload. Vérifie que c'est bien un fichier PDF.";
    this.erreur.set(detail);
  }
});
  }

  envoyerQuestion() {
    const texteQuestion = this.question.trim();
    if (!texteQuestion || this.questionEnCours()) return;

    this.ajouterMessage({ role: 'user', texte: texteQuestion });
    this.question = '';
    this.questionEnCours.set(true);

    this.pdfService.askQuestion(texteQuestion, this.documentSelectionne()).subscribe({
      next: (res) => {
        this.ajouterMessage({
          role: 'assistant',
          texte: res.reponse,
          extraits: res.extraits_utilises
        });
        this.questionEnCours.set(false);
      },
      error: () => {
        this.ajouterMessage({
          role: 'assistant',
          texte: "Erreur : impossible d'obtenir une réponse. Vérifie que les services tournent bien."
        });
        this.questionEnCours.set(false);
      }
    });
  }
}