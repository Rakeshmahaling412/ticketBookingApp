import { Router } from '@angular/router';

import { AuthenticationService } from '../../../../../shared/services/authentication/authentication.service';
import { ObaPiSummary } from '../model/oba-pi-summary.model';
import { ObaPiType } from '../model/oba-pi-type.enum';
import { ConfigCountry } from '../form-config/config.interface';
import { configCountry } from '../form-config/configuration.setting';

export abstract class UIService {

    type: ObaPiType;

    protected constructor(protected readonly router: Router,
                          protected readonly authenticationService: AuthenticationService) {
        this.setTypeFromUrl(this.router.url);
    }

    navigateToRequesterDetail(data: ObaPiSummary): void {
        this.router.navigate([this.url, data.id]);
    }

    navigateToAdminDetail(data: ObaPiSummary): void {
        this.router.navigate([this.url, 'admin', data.id]);
    }

    navigateToManagerDetail(data: ObaPiSummary): void {
        this.router.navigate([this.url, 'manager', data.id]);
    }

    navigateToSupplementalApproverDetail(data: ObaPiSummary): void {
        this.router.navigate([this.url, 'supplemental', data.id]);
    }

    configFactory(activity: string): ConfigCountry {
        return configCountry.find(f => f.activity === activity && f.country === this.authenticationService.currentUser().country);
    }

    private setTypeFromUrl(url: string): void {
        if (url.includes('oba')) {
            this.type = ObaPiType.OBA;
        } else if (url.includes('pi')) {
            this.type = ObaPiType.PI;
        }
    }

    protected get url(): string {
        switch (this.type) {
            case ObaPiType.OBA:
                return 'disclosures/oba';
            case ObaPiType.PI:
                return 'disclosures/pi';
            default:
                return '';
        }
    }

}
