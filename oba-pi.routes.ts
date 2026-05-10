import { Routes } from '@angular/router';

import { features } from '../../../shared/constants/features.constant';
import { PermissionsGuard } from '../../../shared/guards/permissions.guard';
import { OnBehalfObaPiDisclosureDetailComponent } from './oba-pi-detail/on-behalf-oba-pi-disclosure-detail/on-behalf-oba-pi-disclosure-detail.component';
import { RequesterDetailComponent } from './oba-pi-detail/requester-detail/requester-detail.component';
import { AdminListComponent } from './oba-pi-list/admin-list/admin-list.component';
import { ManagerListComponent } from './oba-pi-list/manager-list/manager-list.component';
import { RequesterListComponent } from './oba-pi-list/requester-list/requester-list.component';
import {ManagerDetailComponent} from './oba-pi-detail/manager-detail/manager-detail.component';
import {AdminDetailComponent} from './oba-pi-detail/admin-detail/admin-detail.component';
import {PerimeterGuard} from '../shared/guards/perimeter.guard';
import { SupplementalApproverListComponent } from './oba-pi-list/supplemental-approver-list/supplemental-approver-list.component';
import { SupplementalApproverDetailComponent } from './oba-pi-detail/supplemental-approver-detail/supplemental-approver-detail.component';

export const OBA_PI_ROUTES: Routes = [
    {
        path: '',
        component: RequesterListComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaSubmit, features.piSubmit]
            }
        }
    },
    {
        path: 'manager',
        component: ManagerListComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaManagerReview, features.piManagerReview]
            }
        }
    },
    {
        path: 'admin',
        component: AdminListComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
//                 only: [features.obaAdminReview, features.piAdminReview, features.piViewAll, features.obaViewAll, features.obaSeglReview, features.obaSupplementalApproverReview, features.piSupplementalApproverReview]
                only: [features.obaAdminReview, features.piAdminReview, features.piViewAll, features.obaViewAll, features.obaSeglReview]
            }
        }
    },
    {
        path: 'on-behalf',
        component: OnBehalfObaPiDisclosureDetailComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [
                    features.obaAdminReview,
                    features.obaViewAll,
                    features.piAdminReview,
                    features.piViewAll,
                    features.obaOnBehalf,
                    features.piOnBehalf
                ]
            }
        }
    },

    {
        path: 'new',
        component: RequesterDetailComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaSubmit, features.piSubmit]
            }
        }
    },
    {
        path: ':id',
        component: RequesterDetailComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaSubmit, features.piSubmit]
            }
        }
    },
    {
        path: 'manager/:id',
        component: ManagerDetailComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaManagerReview, features.piManagerReview]
            }
        }
    },
    {
        path: 'admin/:id',
        component: AdminDetailComponent,
        canActivate: [PermissionsGuard, PerimeterGuard],
        data: {
            permissions: {
                only: [features.obaAdminReview, features.piAdminReview, features.obaViewAll, features.piViewAll, features.obaSeglReview, features.obaSupplementalApproverReview, features.piSupplementalApproverReview]
            },
            key: 'OBA_PI_DISCLOSURE'
        }
    },
    {
        path: 'supplemental',
        component: SupplementalApproverListComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaSupplementalApproverReview, features.piSupplementalApproverReview]
            }
        }
    },
    {
        path: 'supplemental/:id',
        component: SupplementalApproverDetailComponent,
        canActivate: [PermissionsGuard],
        data: {
            permissions: {
                only: [features.obaSupplementalApproverReview, features.piSupplementalApproverReview]
            }
        }
    }
];
