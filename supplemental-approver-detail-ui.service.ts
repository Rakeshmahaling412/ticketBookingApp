import { Inject, Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

import { AuthenticationService } from '../../../../../shared/services/authentication/authentication.service';
import { WorkflowConfigService } from '../../../shared/services/workflow-config.service';
import { WorkflowStatus } from '../../shared/constants/workflow-status.enum';
import { ObaPiModel } from '../../shared/model/oba-pi.model';
import { ObaPiService } from '../../shared/services/oba-pi.service';
import { DetailUIService } from '../detail-ui.service';

@Injectable()
export class SupplementalApproverDetailUIService extends DetailUIService {

    constructor(@Inject(Router) router,
                @Inject(AuthenticationService) authenticationService,
                @Inject(ObaPiService) obaPiService,
                @Inject(WorkflowConfigService) workflowConfigService) {
        super(router, authenticationService, obaPiService, workflowConfigService);
    }

    navigateToList(): void {
        this.router.navigate([this.url, 'supplemental']);
    }

    getById(id: string): Observable<ObaPiModel> {
        return this.obaPiService.getById(this.type, id);
    }

    isFieldReadOnlyByStatus(field: string, workflowStatus: string): boolean {
        switch (field) {
            case 'comments':
                return [
                    WorkflowStatus.PendingValidationSupplementalApprover.toString(),
                    WorkflowStatus.PendingValidationAdmin.toString(),
                    WorkflowStatus.Approved.toString()
                ].includes(workflowStatus);
            case 'form':
            case 'lineManager':
            case 'ADDITIONAL_INFORMATION':
                return [
                    WorkflowStatus.Approved.toString()
                ].includes(workflowStatus);
            case 'documents':
                return false;
            default:
                return false;
        }
    }

    exportPdf(id: any, language: any, fullAuditList: any) {
        return this.obaPiService.exportPdf(id, language, fullAuditList);
    }
}

