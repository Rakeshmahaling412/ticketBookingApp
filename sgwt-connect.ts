import { setupSGWTConnect, SGWTConnectCore } from '@sgwt/connect-angular';
import { environment } from './environments/environment';

interface SgwtConnectHTMLElement extends HTMLElement {
    sgwtConnect: SGWTConnectCore;
    setSgwtConnectInstance: (sgwtConnect: SGWTConnectCore) => void;
}

// This is a sample SG Connect Client ID for use in testing our whiteapp.
export const sgwtConnect = setupSGWTConnect({
    authorization_endpoint: environment.authorization_endpoint,
    client_id: environment.client_id,
    scope: 'openid profile api.pad--notification.v1 api.pad-policies.v1 api.pad-accounts.v1 api.personal-account-dealing-pre-approval.v1 api.personal-account-dealing-oba-pi.v1 api.personal-account-dealing-reconciliation.v1',
    // Redirection is made to a dedicated page, cf. explanations in that file.
    redirect_uri: environment.redirect_uri
});




// Now, pass the sgwtConnect instance to the widget
const widget = document.querySelector<SgwtConnectHTMLElement>('sgwt-connect');
if (widget) {
    // When the code is executed, the widget may not be been fully initialized.
    // So, to verify that, we check the existence of the `widget.setSgwtConnectInstance()` function.
    // If it is not the case, we wait for the 'sgwt-connect--ready' event.
    if (typeof widget.setSgwtConnectInstance === 'function') {
        // Widget is already initialized...
        widget.setSgwtConnectInstance(sgwtConnect);
    } else {
        // Widget is not initialized yet, so we will wait the event that indicates the widget is ready...
        const handleSgwtConnectReady = () => {
            widget.setSgwtConnectInstance(sgwtConnect);
            // Remove the event listener
            widget.removeEventListener('sgwt-connect--ready', handleSgwtConnectReady);
        };

        widget.addEventListener('sgwt-connect--ready', handleSgwtConnectReady);
    }
}
