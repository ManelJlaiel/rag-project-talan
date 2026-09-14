import { Injectable, signal } from '@angular/core';
import { OAuthService } from 'angular-oauth2-oidc';
import { authConfig } from '../auth.config';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  estConnecte = signal(false);
  nomUtilisateur = signal<string | null>(null);
  estAdmin = signal(false);

  constructor(private oauthService: OAuthService) {
    this.oauthService.configure(authConfig);

    this.oauthService.loadDiscoveryDocumentAndTryLogin().then(() => {
      this.mettreAJourEtat();
      this.oauthService.setupAutomaticSilentRefresh();
    });

    this.oauthService.events.subscribe(() => {
      this.mettreAJourEtat();
    });
  }

  private mettreAJourEtat() {
    const connecte = this.oauthService.hasValidAccessToken();
    this.estConnecte.set(connecte);

    if (connecte) {
      const claims = this.oauthService.getIdentityClaims() as any;
      this.nomUtilisateur.set(claims?.['preferred_username'] ?? claims?.['name'] ?? 'Utilisateur');
      this.estAdmin.set(this.possedeLeRoleAdmin());
    } else {
      this.nomUtilisateur.set(null);
      this.estAdmin.set(false);
    }
  }

  /**
   * Keycloak place les rôles du realm dans l'access token (pas dans les
   * "identity claims" habituels) sous la structure realm_access.roles.
   * On décode donc directement le token pour aller les chercher.
   */
  private possedeLeRoleAdmin(): boolean {
    const token = this.oauthService.getAccessToken();
    if (!token) return false;

    try {
      const payloadBase64 = token.split('.')[1];
      const payloadJson = decodeURIComponent(
        atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'))
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(payloadJson);
      const roles: string[] = payload?.realm_access?.roles ?? [];
      return roles.includes('admin');
    } catch {
      return false;
    }
  }

  login() {
    this.oauthService.initCodeFlow();
  }

  logout() {
    this.oauthService.logOut();
  }

  getToken(): string {
    return this.oauthService.getAccessToken();
  }
}