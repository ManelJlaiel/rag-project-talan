import { ApplicationConfig, provideBrowserGlobalErrorListeners, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { OAuthModule } from 'angular-oauth2-oidc';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),

    
    provideHttpClient(withInterceptorsFromDi()),

    importProvidersFrom(
      OAuthModule.forRoot({
        resourceServer: {
          
          allowedUrls: ['http://localhost:8082'],
          sendAccessToken: true,
        },
      })
    ),
  ]
};