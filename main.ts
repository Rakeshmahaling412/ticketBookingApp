import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { SGWTConnect } from '@sgwt/connect-angular';

import { AppModule } from './app/app.module';
import { environment } from './environments/environment';
import { LicenseManager } from 'ag-grid-enterprise';

if (environment.production) {
    enableProdMode();
}

LicenseManager.setLicenseKey(
    '<REPLACE_AGGRID_LICENSE_KEY>');

interface ISgwtConnectJWTClaims {
    sub: string;
}

export interface ISgwtConnectElement extends HTMLElement {
    sgwtConnect: SGWTConnect;
}

const wrapper = document.querySelector('sgwt-connect') as ISgwtConnectElement;

const handleSgwtConnectReady = () => {
    const sgwtConnect = wrapper.sgwtConnect;
    // Request authorization, then retrieve the user profile
    if (sgwtConnect.isAuthorized()) {
        // Bootstrap your application...
        platformBrowserDynamic().bootstrapModule(AppModule).catch(err => console.log(err));
    } else if (sgwtConnect.getAuthorizationError()) {
        document.body.innerHTML = `
      <div class="alert alert-danger" role="alert">
        Authorization error: ${sgwtConnect.getAuthorizationError()}.
      </div>
    `;
    } else {
        sgwtConnect.requestAuthorization();
    }
};

if (wrapper.sgwtConnect) {
    handleSgwtConnectReady();
} else {
    wrapper.addEventListener('sgwt-connect--ready', handleSgwtConnectReady);
}
