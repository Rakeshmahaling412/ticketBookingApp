import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { AgGridModule } from 'ag-grid-angular';
import { FileUploadModule } from 'ng2-file-upload';
import { TypeaheadModule } from 'ngx-bootstrap/typeahead';

import { SharedComponentsModule } from '../../../shared/components/shared-components.module';
import { DynamicFormModule } from '../../../shared/modules/dynamic-form/dynamic-form.module';
import { DisclosuresSharedModule } from '../shared/disclosures-shared.module';
import { AdminDetailComponent } from './oba-pi-detail/admin-detail/admin-detail.component';
import { ManagerDetailComponent } from './oba-pi-detail/manager-detail/manager-detail.component';
import { OnBehalfObaPiDisclosureDetailComponent } from './oba-pi-detail/on-behalf-oba-pi-disclosure-detail/on-behalf-oba-pi-disclosure-detail.component';
import { RequesterDetailUIService } from './oba-pi-detail/requester-detail/requester-detail-ui.service';
import { RequesterDetailComponent } from './oba-pi-detail/requester-detail/requester-detail.component';
import { AdminListComponent } from './oba-pi-list/admin-list/admin-list.component';
import { ManagerListComponent } from './oba-pi-list/manager-list/manager-list.component';
import { RequesterListComponent } from './oba-pi-list/requester-list/requester-list.component';
import { SupplementalApproverListComponent } from './oba-pi-list/supplemental-approver-list/supplemental-approver-list.component';
import { SupplementalApproverDetailComponent } from './oba-pi-detail/supplemental-approver-detail/supplemental-approver-detail.component';
import { OBA_PI_ROUTES } from './oba-pi.routes';
import { OBA_PI_DYNAMIC_COMPONENTS } from './shared/components/oba-pi-dynamic-components';
import { ObaPiService } from './shared/services/oba-pi.service';
import { ValidatorService } from './shared/services/validator.service';

@NgModule({
    declarations: [
        RequesterDetailComponent,
        RequesterListComponent,
        ManagerListComponent,
        AdminListComponent,
        ManagerDetailComponent,
        AdminDetailComponent,
        ...OBA_PI_DYNAMIC_COMPONENTS,
        OnBehalfObaPiDisclosureDetailComponent,
        SupplementalApproverListComponent,
        SupplementalApproverDetailComponent
    ],
    imports: [
        HttpClientModule,
        AgGridModule.withComponents([]),
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        TypeaheadModule.forRoot(),
        RouterModule.forChild(OBA_PI_ROUTES),
        TranslateModule,
        SharedComponentsModule,
        FileUploadModule,
        DisclosuresSharedModule,
        DynamicFormModule
    ],
    providers: [ObaPiService, ValidatorService, RequesterDetailUIService]
})
export class ObaPiModule {
}
