import {Component, EventEmitter, Input, OnDestroy, OnInit, Output, ViewChild} from '@angular/core';
import {AbstractControl, FormControl, FormGroup, Validators} from '@angular/forms';
import {Subject} from 'rxjs';
import {NgxPermissionsService} from 'ngx-permissions';
import {takeUntil} from 'rxjs/operators';

import {DynamicUiService} from '../../../../../../shared/services/dynamic-ui/dynamic-ui.service';
import {ProductType} from '../../model/product-type.model';
import {Trade} from '../../model/trade.model';
import {ProductTypeService} from '../../services/product-type.service';
import {TradeUIService} from '../trade-approval-form/trade-ui.service';
import {SecuritySearchComponent} from './components/security-search/security-search.component';
import {features} from '../../../../../../shared/constants/features.constant';
import {ITradeDropdownDataInterface} from './components/trade-dropdown/trade-dropdown-data.interface';
import {TradeOperation} from '../../model/enums/trade-operation.enum';
import {ValidatorsUtils} from '../../../../../../shared/utils/validators.utils';
import {AuthenticationService} from '../../../../../../shared/services/authentication/authentication.service';
import {CustomValidators} from '../../../../../../shared/validators/custom.validators';
import {Country} from '../../../../../../shared/services/feature-country/country.constants';
import { TradeApprovalService } from '../../services/trade-approval.service';
import { AlertService } from '../../../../../../shared/components/alert/alert.service';
import { BsModalRef, BsModalService } from 'ngx-bootstrap/modal';

@Component({
    selector: 'pad-trade-form',
    templateUrl: './trade-form.component.html'
})
export class TradeFormComponent implements OnInit, OnDestroy {

    private static readonly IPO = 'IPO';
    private static readonly ESOP = 'ESOP';

    @Input() requestStatus: string;
    @Input() approvalForm: FormGroup;
    @Input() readonly: boolean;
    @Input() requesterGgi: string;
    @Input() requesterCountry: string;
    @Input() forceDisplayPersonalInformation = false;

    @Input() set trade(input: Trade) {
        this.initTradeForm(input);
    }

    @Output() add = new EventEmitter<FormGroup>();
    @Output() save = new EventEmitter<FormGroup>();
    @Output() cancel = new EventEmitter<void>();
    @ViewChild(SecuritySearchComponent) securitySearch;
    @ViewChild('alertpopup', {static: true}) alertpopupRef;

    form: FormGroup;
    mode: 'add' | 'edit';
    isSubmitted: boolean;
    securityReadOnly = true;
    totalValueComponent: string;
    held30DaysComponent: string;
    valueDroppedComponent: string;
    isNewOrSavedAsDraft: boolean;
    hasViewPersonalInformationFeature: boolean;
    private readonly unsubscribe = new Subject();
    tradeDropDownComponent: string;
    modalRef: BsModalRef;
    isControlRequired = ValidatorsUtils.isControlRequired;

    productTypes: ProductType[];
    isManualSecuritySearch: boolean;

    constructor(private readonly tradeUIService: TradeUIService,
                private readonly permissionsService: NgxPermissionsService,
                private readonly dynamicUiService: DynamicUiService,
                private readonly authenticationService: AuthenticationService,
                private readonly preApprovalService: TradeApprovalService,
                private readonly modalService: BsModalService,
                private readonly alertService: AlertService,
                private readonly productTypeService: ProductTypeService) {
        this.form = tradeUIService.getInitialForm();
        if ([Country.US, Country.CA, Country.BR].includes(this.country)) {
            dynamicUiService.getComponentNameByKey('TRADE_DROP_DOWN').pipe(takeUntil(this.unsubscribe))
                .subscribe(result => this.tradeDropDownComponent = result);
        } else {
            dynamicUiService.getComponentNameByKey('TRADE_HELD_30_DAYS').pipe(takeUntil(this.unsubscribe))
                .subscribe(result => this.held30DaysComponent = result);
            dynamicUiService.getComponentNameByKey('TRADE_VALUE')
                .pipe(takeUntil(this.unsubscribe))
                .subscribe(result => this.totalValueComponent = result);
        }
        this.productTypeService.getAll().pipe(takeUntil(this.unsubscribe))
            .subscribe(productTypes => this.productTypes = productTypes);
    }

    ngOnInit(): void {
        this.setHasViewPersonalInformationFeature();
        this.onGtcOrderCountryChanges();
        this.isNewOrSavedAsDraft = ['NEW', 'SAVED_AS_DRAFT', 'NEW_ON_BEHALF'].includes(this.approvalForm.get('status').value);
    }

    private setHasViewPersonalInformationFeature() {
        if (this.forceDisplayPersonalInformation) {
            this.hasViewPersonalInformationFeature = true;
        } else {
            this.permissionsService.hasPermission(features.viewPersonalInformation)
                .then(hasPermission => this.hasViewPersonalInformationFeature = hasPermission);
        }
    }

    onAdd(): void {
        this.isSubmitted = true;
        if (this.form.valid) {
            if (this.currency && this.currency.value) {
                this.currency.setValue(this.currency.value.toUpperCase());
            }
            const requestorESGEstatus = this.approvalForm.get('esgeStatus').value;
            if (requestorESGEstatus !== null  && (requestorESGEstatus === 'ESGE31' || requestorESGEstatus === 'ESGE45') && this.isNewOrSavedAsDraft) {
                const companyId = this.form.get('security').value.companyId;
                const isGtcOrder = this.form.get('isGTCOrder').value;
                this.checkSGInsider(companyId, isGtcOrder, this.mode);
            } else {
                this.addToGridOnAdd();
            }
        }
    }

    async getSgInsider(companyId: any, isGtcOrder: any, mode: any) {
        const result = new Subject<any>();
        this.preApprovalService.getSGInsiderData(companyId,isGtcOrder,this.requesterGgi).subscribe(
            data => {
                if (!data) {
                    mode === 'add' ? this.addToGridOnAdd() : this.saveToGridOnSave();
                } else {
                    this.modalRef = this.modalService.show(this.alertpopupRef);
                }
                result.next(data);
            }
        );
    }

    onCloseAlertPopup(): void {
        this.modalRef.hide();
    }

    addToGridOnAdd(): void {
        this.add.emit(this.form.getRawValue());
        this.onReset();
    }

    get currency(): AbstractControl {
        return this.form.get('currency');
    }

    get valueIncreased(): AbstractControl {
        return this.form.get('isValueIncreased');
    }

    get valueDropped(): AbstractControl {
        return this.form.get('isValueDropped');
    }

    get shortSale(): AbstractControl {
        return this.form.get('isShortSale');
    }

    get quantity(): AbstractControl {
        return this.form.get('quantity');
    }

    get productType(): AbstractControl {
        return this.form.get('productType');
    }

    get totalValue(): AbstractControl {
        return this.form.get('totalValue');
    }

    get gtcOrder(): AbstractControl {
        return this.form.get('isGTCOrder');
    }

    onSave(): void {
        this.isSubmitted = true;
        if (this.form.valid) {
            const requestorESGEstatus = this.approvalForm.get('esgeStatus').value;
            if (requestorESGEstatus !== null  && (requestorESGEstatus === 'ESGE31' || requestorESGEstatus === 'ESGE45') && this.isNewOrSavedAsDraft) {
                const companyId = this.form.get('security').value.companyId;
                const isGtcOrder = this.form.get('isGTCOrder').value;
                this.checkSGInsider(companyId,isGtcOrder,this.mode)
            } else {
                this.saveToGridOnSave();
            }
        }
    }

    saveToGridOnSave(): void {
        this.save.emit(this.form.getRawValue());
    }

    onReset(): void {
        if (this.securitySearch) {
            this.securitySearch.reset();
        }
        this.form.reset(new Trade());
        this.isSubmitted = false;
        this.securityReadOnly = true;
        this.disableFormControl(this.price);
    }

    onReadOnlySecurityChanged(securityReadOnly: boolean) {
        this.securityReadOnly = securityReadOnly;
    }

    get isSecurityReadOnly(): boolean {
        return !this.readonly ? this.securityReadOnly : true;
    }

    private initTradeForm(trade: Trade): void {
        this.form.patchValue(trade);
        this.mode = trade && (trade.id || trade.productType?.name) ? 'edit' : 'add';
    }

    get operation(): AbstractControl {
        return this.form.get('operation');
    }

    get heldFor30Days(): AbstractControl {
        return this.form.get('isHeldFor30Days');
    }

    get coverShortPosition(): AbstractControl {
        return this.form.get('isCoverShortPosition');
    }

    get price() {
        return this.form.get('price') as FormControl;
    }

    get country() {
        return this.authenticationService.currentUser().country;
    }

    get securityCode(): AbstractControl {
        return this.form.get('security.securityCode');
    }

    get securityType(): AbstractControl {
        return this.form.get('security.code');
    }

    get account(): AbstractControl {
        return this.form.get('account');
    }

    onCancel() {
        this.cancel.emit();
    }

    ngOnDestroy(): void {
        this.unsubscribe.next();
        this.unsubscribe.complete();
    }

    disableFormControl(field: FormControl) {
        if (field != null) {
            field.clearValidators();
            field.disable();
        }
    }

    get heldFor30DaysData(): ITradeDropdownDataInterface {
        return {
            formControlName: 'isHeldFor30Days',
            dependentControlNames: ['operation', 'isCoverShortPosition'],
            onFieldChanged: () => this.onOperationChangeAndCoverShortPositionChange()
        };
    }

    get coverShortPositionData(): ITradeDropdownDataInterface {
        return {
            formControlName: 'isCoverShortPosition',
            dependentControlNames: ['operation'],
            onFieldChanged: () => this.onOperationChangesForCoverShortPosition()
        };
    }

    get valueIncreaseData(): ITradeDropdownDataInterface {
        return {
            formControlName: 'isValueIncreased',
            dependentControlNames: ['isHeldFor30Days'],
            onFieldChanged: () => this.onOperationBuyAndHeldFor30DaysChanges()
        };
    }

    get valueDropData(): ITradeDropdownDataInterface {
        return {
            formControlName: 'isValueDropped',
            dependentControlNames: ['isHeldFor30Days'],
            onFieldChanged: () => this.onOperationSellAndHeldFor30DaysChanges()
        };
    }


    get shortSellData(): ITradeDropdownDataInterface {
        return {
            formControlName: 'isShortSale',
            dependentControlNames: ['isValueDropped'],
            onFieldChanged: () => this.onValueChanges()
        };
    }

    onValueChanges(): boolean {
        const isValueDroppedChanged: boolean = this.valueDropped.value;
        if (isValueDroppedChanged === false) {
            this.shortSale.enable();
            this.shortSale.setValidators([Validators.required, CustomValidators.isNotFalse()]);
            this.shortSale.updateValueAndValidity();
            return true;
        } else {
            return this.updateFormControlStatus(this.shortSale, false);
        }
    }

    onOperationBuyAndHeldFor30DaysChanges(): boolean {
        const operation: TradeOperation = this.operation.value;
        const isHeldFor30Days: boolean = this.heldFor30Days.value;
        if (operation === TradeOperation.BUY && isHeldFor30Days === false) {
            this.valueIncreased.enable();
            this.valueIncreased.setValidators([Validators.required, CustomValidators.isBuyAndHold30daysAndValueDrop()]);
            this.valueIncreased.updateValueAndValidity();
            return true;
        } else {
            return this.updateFormControlStatus(this.valueIncreased, false);
        }
    }

    onOperationSellAndHeldFor30DaysChanges(): boolean {
        const operation: TradeOperation = this.operation.value;
        const isHeldFor30Days: boolean = this.heldFor30Days.value;
        if (operation === TradeOperation.SELL && isHeldFor30Days === false) {
            this.valueDropped.enable();
            this.valueDropped.setValidators(Validators.required);
            this.valueDropped.updateValueAndValidity();
            return true;
        } else {
            return this.updateFormControlStatus(this.valueDropped, false);
        }
    }

    onOperationChangeAndCoverShortPositionChange(): boolean {
        const operation: TradeOperation = this.operation.value;
        const coverShortPosition: boolean = this.coverShortPosition.value;
        if (operation === TradeOperation.SELL || coverShortPosition === true) {
            return this.updateFormControlStatus(this.heldFor30Days, true);
        } else {
            return this.updateFormControlStatus(this.heldFor30Days, false);
        }
    }

    onOperationChangesForCoverShortPosition(): boolean {
        const operation: TradeOperation = this.operation.value;
        return this.updateFormControlStatus(this.coverShortPosition, operation === TradeOperation.BUY);
    }

    onGtcOrderCountryChanges(): void {
        if(![Country.US, Country.CA,Country.BR].includes(this.country)){
            this.updateFormControlStatus(this.gtcOrder, false)
        }
    }

    updateFormControlStatus(formControl: AbstractControl, active: boolean): boolean {
        if (active) {
            formControl.enable();
            formControl.setValidators(Validators.required);
        } else {
            formControl.setValue(null);
            formControl.disable();
            formControl.setValidators([]);
        }
        formControl.updateValueAndValidity();
        return active;
    }

    manualSecuritySearch(isManual: boolean): void {
        this.isManualSecuritySearch = isManual;
        this.securityReadOnly = true;
    }

    ManageValidatorsWhenProductTypeIsIpoOrEsop() {
        if (this.productType.value?.name === TradeFormComponent.IPO || this.productType.value?.name === TradeFormComponent.ESOP) {
            this.form.get('account').disable();
            this.quantity.clearValidators();
            this.quantity.setErrors(null);
            this.totalValue.clearValidators();
            this.totalValue.setErrors(null);
            this.securityCode.clearValidators();
            this.securityType.clearValidators();
        } else {
            this.form.get('account').enable();
            this.quantity.setValidators([Validators.required, Validators.min(0)]);
            if (this.totalValueComponent) {
                this.totalValue.setValidators(Validators.required);
            }
            this.securityCode.setValidators(Validators.required);
            this.securityType.setValidators(Validators.required);
        }
        return (this.productType.value?.name !== TradeFormComponent.IPO && this.productType.value?.name !== TradeFormComponent.ESOP) ;
    }
    ResetSearchBy(value:boolean){
        if(value){
            this.securitySearch.reset();
        }
    }

    private checkSGInsider(companyId: any, isGtcOrder: any, mode: "add" | "edit") {
        if(companyId === null){
            const security = this.form.get('security').value;
            this.preApprovalService.searchByType(security.code.toLowerCase(),security.securityCode.trim().toUpperCase(),0,null,null,this.productType.value.name)
                .subscribe((response:any)=> {
                    if (response.bloombergSecurities.length === 0){
                        this.getSgInsider(companyId,isGtcOrder,mode);
                    }
                    companyId = response.bloombergSecurities[0].companyId;
                    this.getSgInsider(companyId,isGtcOrder,mode);
                });

        }else{
            this.getSgInsider(companyId,isGtcOrder,mode);
        }
    }
}
