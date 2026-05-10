import { Component } from '@angular/core';
import { Router } from '@angular/router';

import {RoleConstants} from "../../shared/constants/role.enum";
import { features } from '../../shared/constants/features.constant';
import { AuthenticationService } from '../../shared/services/authentication/authentication.service';
import { DynamicUiService } from '../../shared/services/dynamic-ui/dynamic-ui.service';
import { EsgeDataService } from 'src/app/shared/utils/esgeDataService';
import {TranslateService} from "@ngx-translate/core";
import {Subscription} from "rxjs";

@Component({
    selector: 'pad-disclosures',
    templateUrl: './disclosures.component.html'
})
export class DisclosuresComponent {

    // routes where tabs + buttons are visible
    private readonly DASHBOARD_ROUTES_HEADER: string[] = [
        '/disclosures/todo/employee',
        '/disclosures/todo/admin',
        '/disclosures/todo/manager',
        '/disclosures/accounts',
        '/disclosures/accounts/admin',
        '/disclosures/dashboard/admin',
        '/disclosures/dashboard/manager-weekly-report',
        '/disclosures/dashboard/on-behalf-manager-weekly-report',
        '/disclosures/dashboard/quarterly-transaction-report',
        '/disclosures/oba',
        '/disclosures/oba/admin',
        '/disclosures/oba/manager',
        '/disclosures/oba/supplemental',
        '/disclosures/pi',
        '/disclosures/pi/admin',
        '/disclosures/pi/manager',
        '/disclosures/pi/supplemental',
        '/disclosures/certifications/admin',
        '/disclosures/trade-approvals',
        '/disclosures/trade-approvals/admin',
        '/disclosures/trade-approvals/manager',
        '/disclosures/trade-approvals/transactions/admin',
        '/disclosures/todo/designated-supervisor',
        '/disclosures/trade-approvals/reconciliations/admin',
        '/disclosures/dashboard/annual-holdings-report',
        '/disclosures/my-profile'
    ];
    private readonly subscriptions = new Subscription();
    quickActionsComponents: string;
    isBrazil: boolean;
    country: string;
    esgeStatus: string | null = null;
    esgeClosingPeriod: string | null = null;
    tradeStatus: string;
    esgeStatusFromService : string
    protected readonly RoleConstants = RoleConstants;
    constructor(private readonly router: Router,
                private readonly authenticationService: AuthenticationService,
                private readonly dynamicUIService: DynamicUiService,
                private readonly esgeDataService: EsgeDataService,
                private readonly translateService: TranslateService) {
        this.isBrazil = this.authenticationService.currentUser().country === 'BR' ? true : false;
        this.country = this.authenticationService.currentUser().country;
        this.dynamicUIService.getComponentNameByKey('QUICK_ACTIONS')
            .subscribe((quickActionsComponents: string) => this.quickActionsComponents = quickActionsComponents);
        }
    ngOnInit(): void {
        this.subscriptions.add(
            this.esgeDataService.getEsgeStatus().subscribe(status => {
                this.esgeStatusFromService = status;
                this.esgeStatus = status ? `SG Insider - ${status}` : null;
                this.calculateTradeStatus();
            })
        );

        this.subscriptions.add(
            this.esgeDataService.getEsgeClosingPeriod().subscribe(period => {
                this.esgeClosingPeriod = period;
                console.log((this.esgeClosingPeriod))
                this.calculateTradeStatus();
            })
        );
    }

    ngOnDestroy(): void {
        this.subscriptions.unsubscribe();
    }
    get features() {
        return features;
    }    

    get isTabVisible(): boolean {
        if(this.router.url.startsWith('/disclosures/dashboard/manager-weekly-report')){
            return true;
        }
        return this.DASHBOARD_ROUTES_HEADER.indexOf(this.router.url) > -1;
    }

    get activeRole(): string {
        return this.authenticationService.currentUser().activatedRole.name;
    }
    get activeRoleKeyName(): string {
        return this.authenticationService.currentUser().activatedRole.keyName;
    }

    get isDesignatedSupervisor(): boolean {
        return this.activeRole === 'Designated supervisor';
     }

    get isCampaignReviewer(): boolean {
        return this.activeRole === 'Campaign reviewer';
    }

    get isCountryUSorCA(): boolean {
        return this.country === 'US' || this.country === 'CA';
    }
    private calculateTradeStatus(): void {
        if ((this.esgeStatusFromService === 'ESGE45' || this.esgeStatusFromService === 'ESGE31') && this.esgeClosingPeriod) {
            const match = this.esgeClosingPeriod.match(/(\d{2}-[A-Za-z]{3}-\d{4}) to (\d{2}-[A-Za-z]{3}-\d{4})/);
            if (match) {
                const startDate = new Date(match[1]);
                const endDate = new Date(match[2]);
                const currentDate = new Date();
                if (currentDate >= startDate && currentDate <= endDate) {
                    this.tradeStatus = this.translateService.instant('NAVBAR.PROHIBITED');
                } else {
                    this.tradeStatus = this.translateService.instant('NAVBAR.FREE_TO_TRADE');
                }
            }
        }
        else {
            if (this.esgeStatusFromService === 'ESGE45' || this.esgeStatusFromService === 'ESGE31') {
                this.tradeStatus = this.translateService.instant('NAVBAR.FREE_TO_TRADE');
            } else {
                this.tradeStatus = null;
            }
        }
    }

}
