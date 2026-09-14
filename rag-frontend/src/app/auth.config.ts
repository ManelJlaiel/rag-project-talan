import { AuthConfig } from 'angular-oauth2-oidc';

export const authConfig: AuthConfig = {
  
  issuer: 'http://localhost:8180/realms/talan-stage',

 
  redirectUri: window.location.origin,

  clientId: 'rag-frontend',


  responseType: 'code',

 
  scope: 'openid profile email',

  
  requireHttps: false,

  
  showDebugInformation: true,
};