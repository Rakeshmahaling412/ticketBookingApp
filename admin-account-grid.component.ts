import {GridOptions} from '@ag-grid-enterprise/all-modules';
import {Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation} from '@angular/core';
import {TranslateService} from '@ngx-translate/core';
import 'ag-grid-enterprise';
import ACCOUNT from '../../../../../../assets/i18n/account/en.json';
import {FILTER_PARAMS} from '../../../../../shared/constants/encrypted-grid.constant';

import moment from 'moment';
import {DocumentModel} from '../../../../../shared/model/document.model';
import {AgGridService} from '../../../../../shared/services/ag-grid/ag-grid.service';
import {AuthenticationService} from '../../../../../shared/services/authentication/authentication.service';
import {DateFormatService} from '../../../../../shared/services/date-format/date-format.service';
import {DocumentService} from '../../../../../shared/services/document/document.service';
import {CommonUtils} from '../../../../../shared/utils/common.utils';
import {AccountSummary} from '../../../accounts/shared/model/account-summary.model';
import {WorkflowAuditModel} from '../workflow-audit/workflow-audit.model';
import {Country} from '../../../../../shared/services/feature-country/country.constants';
import {RoleConstants} from "../../../../../shared/constants/role.enum";


@Component({
    selector: 'pad-admin-account-grid',
    templateUrl: './admin-account-grid.component.html',
    styleUrls: ['./admin-account-grid.component.scss'],
    encapsulation: ViewEncapsulation.None
})
export class AdminAccountGridComponent implements OnInit {

    @Input() data: AccountSummary[];
    @Input() exportEnabled: boolean;
    @Input() title: string;
    @Output() selected = new EventEmitter<string>();
    @Input() gridRows: 10 | 20 = 20;
    @Input() hideToolPanel = false;
    @Input() sort: 'desc' | 'asc' = 'desc';
    @Input() enableExport = true;
    @Input() collapsible = false;
    @Input() serverSide = false;
    @Output() refresh = new EventEmitter();
    @Input() gridName: string;

    gridHeight: number;
    gridOptions: GridOptions;
    sideBar: any = null;
    frameworkComponents: any;
    theme: any = null;
    gridApi: any;
    quickFilterValue: string;
    postProcessPopup: any;
    exportCounter = 0;
    isBrazil: boolean;

    constructor(private readonly agGridService: AgGridService,
                private readonly translateService: TranslateService,
                private readonly documentService: DocumentService,
                private readonly authenticationService: AuthenticationService,
                public readonly dateFormatService: DateFormatService) {
    }

    ngOnInit(): void {
        this.isBrazil = this.authenticationService.currentUser().country === 'BR' ? true : false;
        this.initGridOptions();
        this.gridHeight = this.gridRows === 10 ? 350 : 600;
        if (this.gridOptions) {
            this.gridOptions.onFilterChanged = this.onFilterChanged.bind(this);
            this.gridOptions.onFirstDataRendered = this.onFirstDataRendered.bind(this);
        }
    }

    // Save filter model to localStorage
    onFilterChanged(params): void {
        localStorage.setItem(`${this.gridName}-filterModel`, JSON.stringify(params.api.getFilterModel()));
    }

    // Restore filter model from localStorage
    onFirstDataRendered(params): void {
        const filterModel = localStorage.getItem(`${this.gridName}-filterModel`);
        if (filterModel) {
            params.api.setFilterModel(JSON.parse(filterModel));
        }
    }

    quickFilter(value: string): void {
        this.quickFilterValue = value;
        const data = {
            searchKey: 'ALL',
            searchType: 'contains',
            value
        };

        setTimeout(() => {
            if (this.quickFilterValue === value) {
                this.refresh.emit(data);
            }
        }, 1000);
    }

    exportData(): void {
        this.agGridService.paginateAllPagesForExport(this.gridOptions, this.exportCounter);
        this.exportCounter++;
    }

    onRowClick(event) {
        this.selected.emit(event.data.accountId);
    }

    private initGridOptions(): void {
        this.theme = this.agGridService.getTheme();
        this.frameworkComponents = this.agGridService.getFrameworkComponents();
        this.gridOptions = this.agGridService.initGridOptions(this.getGridColumnDefs());
        this.postProcessPopup = this.agGridService.postProcessPopup;
        this.gridOptions.paginationPageSize = this.gridRows;
        if (this.serverSide) {
            this.agGridService.setServerSideRendering(this.gridOptions);
        }

        this.sideBar = {
            toolPanels: [
                {
                    id: 'columns',
                    labelDefault: 'Columns',
                    labelKey: 'columns',
                    iconKey: 'columns',
                    toolPanel: 'agColumnsToolPanel',
                    toolPanelParams: {
                        suppressRowGroups: true,
                        suppressValues: true,
                        suppressPivots: true,
                        suppressPivotMode: true,
                        suppressColumnFilter: true,
                        suppressColumnSelectAll: true,
                        suppressColumnExpandAll: true
                    }
                }
            ]
        };
    }

    private getGridColumnDefs(): any {
            const columnDefs = [
            {
                headerName: this.translateService.instant('GRID.HR_INFO'),
                children: [
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.CRD'),
                        field: 'requester.crdNumber'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.DEPARTMENT_CODE'),
                        field: 'requester.departmentCode'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.DEPARTMENT_NAME'),
                        field: 'requester.departmentName'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.DESIGNATED_SUPERVISOR'),
                        field: 'requester.designatedSupervisor',
                        sortable: false,
                        valueGetter: params => params.data ? this.getName(params.data.requester.designatedSupervisor) : ''
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.DIVISION'),
                        field: 'requester.division'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.EMPLOYEE_CLASS'),
                        field: 'requester.classDescription'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('EMPLOYEE_EMAIL'),
                        field: 'requester.email',
                        filterParams: FILTER_PARAMS,
                        sortable: false
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.HIRE_DATE'),
                        field: 'requester.hireDate',
                        type: 'dateColumnUTC',
                        filter: false
                    },

                    {
                        hide: true,
                        headerName: this.translateService.instant('EMPLOYEE_REHIRE_DATE'),
                        field: 'requester.reHireDate',
                        type: 'dateColumn',
                        filter: false
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('EMPLOYEE_TERMINATION_DATE'),
                        field: 'requester.terminationDate',
                        type: 'dateColumn',
                        filter: false
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('EMPLOYEE_DESIGNATION'),
                        field: 'requester.designation',
                        valueGetter: params => params.data && params.data.requester && params.data.requester.designation 
                            ? params.data.requester.designation 
                            : '',
                        suppressColumnsToolPanel: this.authenticationService.currentUser().country !== 'US'
                    },
                   {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.HR_STATUS'),
                        field: 'requester.employeeStatus'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.HR_SUPERVISOR'),
                        field: 'requester.hrSupervisor'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.IS_REGISTERED'),
                        field: 'requester.registered',
                        filter: this.serverSide ? 'AgBooleanColumnFilter' : true,
                        valueGetter: params => params.data ? this.booleanToText(params.data.requester.registered) : ''
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTOR_LEGAL'),
                        field: 'requester.legalEntity'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTOR_LEGAL_ID'),
                        field: 'requester.legalEntityId'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.OFFICER_TITLE'),
                        field: 'requester.officerTitle'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.POSITION_TITLE'),
                        field: 'requester.positionTitle'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('REQUESTER.TRADE_REVIEW_MANAGER'),
                        filter: false,
                        sortable: false,
                        valueGetter: params => params.data ? this.getName(params.data.requester.tradeReviewManager) : ''
                    },
                    {
                        headerName: this.translateService.instant('REQUESTOR_FIRST_NAME'),
                        field: 'requester.firstName',
                        valueGetter: params => (params.data && params.data.requester) ? `${params.data.requester.firstName}` : ''
                    },
                    {
                        headerName: this.translateService.instant('REQUESTOR_LAST_NAME'),
                        field: 'requester.lastName',
                        valueGetter: params => (params.data && params.data.requester) ? `${params.data.requester.lastName}` : '',
                        sortable: false
                    },
                    {
                        headerName: this.translateService.instant('COUNTRY'),
                        field: 'country',
                        hide: this.authenticationService.currentUser().perimeter == null,
                        filterParams: {
                            filterOptions: {
                                key: null,
                                values: this.authenticationService.getPerimeterCountries()
                            }
                        },
                        filter: this.serverSide ? 'AgTranslatedColumnFilterComponent' : true
                    }, {
                        hide: false,
                        headerName: this.translateService.instant('Current Country'),
                        field: 'requester.country'
                    },
                ]

            },
            {
                headerName: this.translateService.instant(this.isBrazil ? 'CPF_NUMBER' : 'GRID.BROKERAGE_ACCOUNT'),
                children: [
                    {
                        headerName: this.translateService.instant(this.isBrazil ? 'HOLDER_NAME' : 'ACCOUNT_NAME'),
                        field: 'accountName',
                        filterParams: FILTER_PARAMS,
                        sortable: false
                    },
                    {
                        headerName: this.translateService.instant(this.isBrazil ? 'CPF_NUMBER' : 'ACCOUNT_NUMBER'),
                        field: 'accountNumber',
                        type: 'linkColumn',
                        cellClass: 'stringType',
                        onCellClicked: params => this.selected.emit(params.data.accountId),
                        filterParams: FILTER_PARAMS,
                        sortable: false
                    },
                    {
                        headerName: this.translateService.instant('ACCOUNT_TYPE'), field: 'accountType',
                        valueGetter: params => params.data && params.data.accountType ? this.translateService.instant(`ACCOUNT_TYPE_DATA.${params.data.accountType}`) : '',
                        filterParams: {
                            filterOptions: {key: 'ACCOUNT_TYPE_DATA', values: Object.keys(ACCOUNT.ACCOUNT_TYPE_DATA)}
                        },
                        filter: this.serverSide ? 'AgTranslatedColumnFilterComponent' : true,
                        hide: this.isBrazil
                    },
                    {hide: this.isBrazil, headerName: this.translateService.instant('BROKER_DEALER'), field: 'brokerName'},
                    {
                        headerName: this.translateService.instant('CURRENT_STATUS'),
                        field: 'status',
                        type: 'translatableColumn',
                        filter: false
                    },
                    {headerName: this.translateService.instant('EMPLOYEE_GGI'), field: 'requester.ggi'},
                    {
                        headerName: this.translateService.instant('LAST_MODIFIED'),
                        field: 'lastModifiedDate',
                        type: 'dateColumnWithLocalTimeZone',
                        filter: false
                    },
                    {
                        headerName: this.translateService.instant('ACCOUNT_OPEN_DATE'),
                        field: 'openDate',
                        filter: false,
                        hide: true,
                        valueGetter: params => {
                            const date = params.data ? params.data.openDate : null;
                            return date ? moment.utc(date).format(this.dateFormatService.getDateFormat()) : '';
                        }
                    },
                    {
                        headerName: this.translateService.instant('LINKED'),
                        field: 'linked',
                        filter: this.serverSide ? 'AgBooleanColumnFilter' : true,
                        valueGetter: params => params.data ? this.booleanToText(params.data.linked) : ''
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('CREATED_DATE'),
                        field: 'createdDate',
                        type: 'dateColumnWithLocalTimeZone',
                        filter: false
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('BROKER_TYPE'),
                        field: 'brokerType',
                        type: 'translatableColumn'
                    },
                    {
                        hide: true, headerName: this.translateService.instant('LAST_PUBLIC_COMMENT'),
                        field: 'lastPublicComment',
                        tooltipComponent: 'customTooltip',
                        tooltipField: 'lastPublicComment'
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('LETTER_3210'),
                        cellStyle: {textAlign: 'center'},
                        field: 'documents',
                        cellRenderer: params => this.getDownloadBtn(params.data.documents, 'LETTER_3210', params.colDef.headerName),
                        onCellClicked: params => this.download(params.data.documents, 'LETTER_3210')
                    },
                    {
                        headerName: this.translateService.instant('MANAGED'),
                        field: 'managed',
                        filter: this.serverSide ? 'AgBooleanColumnFilter' : true,
                        valueGetter: params => params.data ? this.booleanToText(params.data.managed) : ''
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('NEGATIVE_LETTER_3210'),
                        cellStyle: {textAlign: 'center'},
                        field: 'documents',
                        cellRenderer: params => this.getDownloadBtn(params.data.documents, 'NEGATIVE_LETTER_3210', params.colDef.headerName),
                        onCellClicked: params => this.download(params.data.documents, 'NEGATIVE_LETTER_3210')
                    },
                    {
                        headerName: this.translateService.instant('REASON'), field: 'reason',
                        valueGetter: params => params.data && params.data.reason ? this.translateService.instant(`REASON_DATA.${params.data.reason}`) : '',
                        filterParams: {
                            filterOptions: {key: 'REASON_DATA', values: Object.keys(ACCOUNT.REASON_DATA)}
                        },
                        filter: this.serverSide ? 'AgTranslatedColumnFilterComponent' : true
                    },
                    {
                        headerName: this.translateService.instant('RELATIONSHIP'), field: 'relationship',
                        valueGetter: params => params.data && params.data.relationship ? this.translateService.instant(`RELATIONSHIP_DATA.${params.data.relationship}`) : '',
                        filterParams: {
                            filterOptions: {key: 'RELATIONSHIP_DATA', values: Object.keys(ACCOUNT.RELATIONSHIP_DATA)}
                        },
                        filter: this.serverSide ? 'AgTranslatedColumnFilterComponent' : true
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('TERMINATION_LETTER'),
                        cellStyle: {textAlign: 'center'},
                        field: 'documents',
                        cellRenderer: params => this.getDownloadBtn(params.data.documents, 'TERMINATION_LETTER', params.colDef.headerName),
                        onCellClicked: params => this.download(params.data.documents, 'TERMINATION_LETTER')
                    },
                    {
                        hide: this.authenticationService.currentUser().country !== Country.HK || this.isBrazil,
                        headerName: this.translateService.instant('BROKER_DEALER_ADDRESS'), 
                        field: 'brokerDealerAddress'},
                    {
                        hide: this.authenticationService.currentUser().country !== Country.HK || this.isBrazil,
                        headerName: this.translateService.instant('BROKER_DEALER_COUNTRY'), 
                        field: 'brokerDealerCountry'
                    }
                ]
            },
            {
                headerName: this.translateService.instant('GRID.AUDIT'),
                children: [
                    {
                        hide: true,
                        headerName: this.translateService.instant('LAST_ACTED_BY_ACTION'),
                        field: 'workflowTasks',
                        valueGetter: params => {
                            const actedBy = params.data && params.data.workflowTasks ? this.getLastWorkflowTask(params.data.workflowTasks).actedBy : null;
                            return actedBy ? this.translateService.instant(actedBy) : '';
                        },
                        filter: false
                    },
                    {
                        hide: true, headerName: this.translateService.instant('LAST_ACTION'), field: 'workflowTasks',
                        valueGetter: params => {
                            const action = params.data && params.data.workflowTasks ? this.getLastWorkflowTask(params.data.workflowTasks).action : null;
                            return action ? this.translateService.instant(`WORKFLOW_ACTION.${action}`) : '';
                        },
                        filter: false
                    },
                    {
                        hide: true,
                        headerName: this.translateService.instant('LAST_ACTOR_ACTION'),
                        field: 'workflowTasks.actor',
                        valueGetter: params => {
                            const actor = params.data && params.data.workflowTasks ? this.getLastWorkflowTask(params.data.workflowTasks).actor : null;
                            return actor ? this.translateService.instant(actor) : '';
                        },
                        filter: false
                    },
                    {
                        headerName: this.translateService.instant('NEXT_ACTION_BY'),
                        field: 'nextActionBy',
                        type: 'translatableColumn'
                    }
                ]
            }
    ];
          // Remove 'accountNumber' column for Audit role
        if (this.authenticationService.activeRole === RoleConstants.Audit) {
            const brokerageGroup = columnDefs.find(group =>
                group.headerName === this.translateService.instant(this.isBrazil ? 'CPF_NUMBER' : 'GRID.BROKERAGE_ACCOUNT')
            );
            if (brokerageGroup?.children) {
                const filteredChildren = [];
                for (const col of brokerageGroup.children) {
                    if ((col as any).field !== 'accountNumber') {
                        filteredChildren.push(col);
                    }
                }
                brokerageGroup.children = filteredChildren;
            }
        }
             return columnDefs;
    }

    onGridReady(params: any) {
        this.gridApi = params.api;
        this.gridApi.closeToolPanel();
        if (this.hideToolPanel) {
            this.gridApi.setSideBarVisible(false);
        }
        this.refresh.emit();
    }

    download(docs: DocumentModel[], type: string) {
        const doc: DocumentModel = this.findDocument(docs, type);
        if (doc && doc.id > 0) {
            this.documentService.getContent(doc).subscribe((data: Blob) => {
                CommonUtils.downloadDocument(data, doc.name);
            });
        }
    }

    private getName(name: any): string {
        const firstName = name.firstName ? name.firstName : '';
        const lastName = name.lastName ? name.lastName : '';
        return name ? `${firstName} ${lastName}` : '';
    }

    private booleanToText(val: boolean): string {
        return val ? this.translateService.instant('YES') : this.translateService.instant('NO');
    }

    private getDownloadBtn(docs: DocumentModel[], type: string, headerName: string): string {
        const doc: DocumentModel = this.findDocument(docs, type);
        return (doc && doc.id > 0)
            ? `<a role="button" class="text-center" title="${headerName}"><em class="icon icon-lg cursor-pointer">save_alt</em></a>`
            : '';
    }

    private findDocument(docs: DocumentModel[], type: string): DocumentModel {
        if (docs) {
            let doc: DocumentModel;
            for (const aDoc of docs) {
                if (aDoc.documentType === type) {
                    doc = aDoc;
                    break;
                }
            }
            return doc;
        } else {
            return null;
        }
    }

    private getLastWorkflowTask(tasks: WorkflowAuditModel[]): WorkflowAuditModel {
        let task: WorkflowAuditModel = new WorkflowAuditModel();
        if (tasks && tasks.length > 0) {
            task = tasks[0];
            tasks.forEach(t => {
                if (new Date(t.actedDate).getTime() > new Date(task.actedDate).getTime()) {
                    task = t;
                }
                return t;
            });
        }
        return task;
    }

    private paginateAllPages(): void {
        const totalPages = this.gridOptions.api.paginationGetTotalPages();
        const currentPage = this.gridOptions.api.paginationGetCurrentPage();
        this.gridOptions.api.paginationGoToFirstPage();
        for (let i = 0; i < totalPages; i++) {
            this.gridOptions.api.paginationGoToNextPage();
        }
        this.gridOptions.api.paginationGoToPage(currentPage);
    }

}
