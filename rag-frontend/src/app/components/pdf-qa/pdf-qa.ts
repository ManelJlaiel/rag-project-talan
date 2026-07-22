import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PdfService } from '../../services/pdf';

interface MessageChat {
  role: 'user' | 'assistant';
  texte: string;
  extraits?: string[];
}

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
  messages = signal<MessageChat[]>([]);
  question = '';

  fichierEnCours = signal(false);
  questionEnCours = signal(false);
  erreur = signal<string | null>(null);

  constructor(private pdfService: PdfService) {
    this.chargerDocuments();
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
        input.value = ''; // reset l'input pour permettre de re-uploader le même fichier
      },
      error: () => {
        this.fichierEnCours.set(false);
        this.erreur.set("Échec de l'upload. Vérifie que c'est bien un fichier PDF.");
      }
    });
  }

  envoyerQuestion() {
    const texteQuestion = this.question.trim();
    if (!texteQuestion || this.questionEnCours()) return;

    this.messages.update(msgs => [...msgs, { role: 'user', texte: texteQuestion }]);
    this.question = '';
    this.questionEnCours.set(true);

    this.pdfService.askQuestion(texteQuestion, this.documentSelectionne()).subscribe({
      next: (res) => {
        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          texte: res.reponse,
          extraits: res.extraits_utilises
        }]);
        this.questionEnCours.set(false);
      },
      error: () => {
        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          texte: "Erreur : impossible d'obtenir une réponse. Vérifie que les services tournent bien."
        }]);
        this.questionEnCours.set(false);
      }
    });
  }
}