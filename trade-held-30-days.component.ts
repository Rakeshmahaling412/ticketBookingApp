import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { AbstractControl, FormGroup, Validators } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { TradeOperation } from '../../../../model/enums/trade-operation.enum';

@Component({
    selector: 'pad-trade-held-30-days',
    templateUrl: './trade-held-30-days.component.html'
})
export class TradeHeld30DaysComponent implements OnInit, OnDestroy {

    @Input() form: FormGroup;
    @Input() readOnly: boolean;
    @Input() formSubmitted: boolean;

    isVisible = false;
    private readonly unsubscribe = new Subject();

    ngOnInit(): void {
        if (this.operation.value) {
            this.onOperationChanged(this.operation.value);
        }
        this.operation.valueChanges
            .pipe(takeUntil(this.unsubscribe))
            .subscribe((operation: TradeOperation) => this.onOperationChanged(operation));
    }

    get operation(): AbstractControl {
        return this.form.get('operation');
    }

    get heldFor30Days(): AbstractControl {
        return this.form.get('isHeldFor30Days');
    }

    private onOperationChanged(operation: TradeOperation): void {
        if (operation === TradeOperation.SELL) {
            this.isVisible = true;
            this.heldFor30Days.enable();
            this.heldFor30Days.setValidators(Validators.required);
            this.heldFor30Days.updateValueAndValidity();
        } else {
            this.heldFor30Days.setValue(null);
            this.heldFor30Days.disable();
            this.heldFor30Days.setValidators([]);
            this.heldFor30Days.updateValueAndValidity();
            this.isVisible = false;
        }
    }

    ngOnDestroy(): void {
        this.unsubscribe.next();
        this.unsubscribe.complete();
    }
}
