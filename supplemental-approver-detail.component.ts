import { Component, OnDestroy, OnInit, ViewChild, AfterContentChecked, ChangeDetectorRef } from '@angular/core';
import { Location } from '@angular/common';
import { FormArray, FormControl, FormGroup, FormBuilder } from '@angular/forms';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { mergeMap, takeUntil } from 'rxjs/operators';
import { AuthenticationService } from '../../../../../shared/services/authentication/authentication.service';
import { DateFormatService } from '../../../../../shared/services/date-format/date-format.service';

import { DynamicUiService } from '../../../../../shared/services/dynamic-ui/dynamic-ui.service';
import { InformationTrailTab } from '../../../accounts/shared/types/information-trail-tab.type';
import { DynamicActionsComponent, WorkflowCommentsComponent } from '../../../shared/components';
import { ActionsRequestParamModel } from '../../../shared/model/action-request-param.model';
import { Action } from '../../../shared/model/action.model';
import { ObaPiModel } from '../../shared/model/oba-pi.model';
import { SupplementalApproverDetailUIService } from './supplemental-approver-detail-ui.service';
import { configCountry } from '../../shared/form-config/configuration.setting';
import { ConfigCountry } from '../../shared/form-config/config.interface';
import { WorkflowStatus } from '../../shared/constants/workflow-status.enum';
import { UserResponse } from '../../shared/model/user-response.model';
import * as moment from 'moment';
import { ObaPiType } from '../../shared/model/oba-pi-type.enum';
import { WorkflowAuditModel } from '../../../shared/components/workflow-audit/workflow-audit.model';
import { WorkflowStatusConstants } from '../../../accounts/shared/constants/workflow-status.constants';
import { MatomoTracker } from 'ngx-matomo';

@Component({
    selector: 'pad-supplemental-approver-oba-pi-detail',
    templateUrl: './supplemental-approver-detail.component.html',
    providers: [SupplementalApproverDetailUIService]
})
export class SupplementalApproverDetailComponent implements OnInit, AfterContentChecked, OnDestroy {

    @ViewChild(WorkflowCommentsComponent) workflowComments;
    @ViewChild(DynamicActionsComponent) workflowActions;

    form: FormGroup;
    isReadOnly: boolean;
    formSubmitted: boolean;
    title: string;
    displayClosureInfoPanel: boolean;
    isRequestOnEditionMode: boolean;
    actionRequestParam: ActionsRequestParamModel;
    activeInformationTrailTab: InformationTrailTab = 'comments';
    policyCategory: string;
    responses: FormGroup;
    obaPi: ObaPiModel;
    config: any;
    configForm: ConfigCountry;
    responseEvent = new Subject<any>();
    configCountry: ConfigCountry[];
    isAnyFieldEditable: boolean;
    actions: Action[];
    currentUser: string;
    auditList: WorkflowAuditModel[] = [];
    fullAuditList: WorkflowAuditModel[] = [];
    exportPdfEnabled = false;

    private readonly unsubscribe = new Subject();

    constructor(
        private readonly route: ActivatedRoute,
        private readonly router: Router,
        private readonly location: Location,
        private readonly fb: FormBuilder,
        private readonly uiService: SupplementalApproverDetailUIService,
        private readonly dynamicUiService: DynamicUiService,
        private readonly authenticationService: AuthenticationService,
        private readonly dateFormatService: DateFormatService,
        private readonly cdRef: ChangeDetectorRef,
        private readonly matomoTracker: MatomoTracker
    ) {}

    ngOnInit(): void {
        this.currentUser = this.authenticationService.getName();
        this.route.params
            .pipe(
                mergeMap((params: Params) => this.uiService.getById(params['id'])),
                takeUntil(this.unsubscribe)
            )
            .subscribe((obaPi: ObaPiModel) => {
                this.obaPi = obaPi;
                this.initForm();
            });
    }

    ngAfterContentChecked(): void {
        this.cdRef.detectChanges();
    }

    ngOnDestroy(): void {
        this.unsubscribe.next();
        this.unsubscribe.complete();
    }

    private initForm(): void {
        this.form = this.fb.group({});
        this.isReadOnly = this.uiService.isFieldReadOnlyByStatus('form', this.obaPi.status);
    }

    navigateToList(): void {
        this.uiService.navigateToList();
    }
}

