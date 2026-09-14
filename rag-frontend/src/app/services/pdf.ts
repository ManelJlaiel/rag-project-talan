import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const API_BASE = 'http://localhost:8082/api/pdf';

export interface UploadResponse {
  message: string;
  nb_chunks: number;
}

export interface AskResponse {
  question: string;
  reponse: string;
  extraits_utilises: string[];
}

export interface DocumentsResponse {
  documents: string[];
}

export interface DeleteResponse {
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class PdfService {

  constructor(private http: HttpClient) {}

  uploadPdf(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${API_BASE}/upload`, formData);
  }

  askQuestion(question: string, document: string | null = null): Observable<AskResponse> {
    return this.http.post<AskResponse>(`${API_BASE}/ask`, { question, document });
  }

  getDocuments(): Observable<DocumentsResponse> {
    return this.http.get<DocumentsResponse>(`${API_BASE}/documents`);
  }

  deleteDocument(nomDocument: string): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${API_BASE}/documents/${encodeURIComponent(nomDocument)}`);
  }
}