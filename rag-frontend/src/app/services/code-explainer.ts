import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// URL de la Gateway Spring Cloud (pas directement le microservice Python)
const API_BASE = 'http://localhost:8082/api/code';

export interface ServiceDetecte {
  dossier: string;
  technologie: string;
  fichier_config: string;
}

export interface EndpointDetecte {
  methode: string;
  route: string;
  fichier: string;
  framework: string;
}

export interface AnalyzeResponse {
  resume: string;
  services_detectes: ServiceDetecte[];
  endpoints_detectes: EndpointDetecte[];
}

@Injectable({
  providedIn: 'root'
})
export class CodeExplainerService {

  constructor(private http: HttpClient) {}

  analyzeRepo(githubUrl: string): Observable<AnalyzeResponse> {
    return this.http.post<AnalyzeResponse>(`${API_BASE}/analyze`, { github_url: githubUrl });
  }
}