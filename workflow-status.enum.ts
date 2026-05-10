export enum WorkflowStatus {
    new = 'NEW',
    SavedAsDraft = 'SAVED_AS_DRAFT',
    PendingValidationControlRoom = 'CONTROL_ROOM_PENDING_VALIDATION',
    Restarted = 'RESTARTED',
    ReworkRequested = 'REWORK_REQUESTED',
    ClosureRequested = 'CLOSURE_REQUESTED',
    ReworkClosureRequested = 'REWORK_CLOSURE_REQUESTED',
    Closed = 'CLOSED',
    System_Closed = 'SYSTEM_CLOSED',
    PendingClosure = 'PENDING_CLOSURE',
    Approved = 'APPROVED',
    PendingValidation = 'PENDING_VALIDATION', // simplified status for PendingValidationAdmin + PendingValidationManager + PendingValidationSupervisor
    PendingValidationAdmin = 'PENDING_VALIDATION_ADMIN',
    PendingValidationManager = 'PENDING_VALIDATION_MANAGER',
    PendingValidationSupervisor = 'PENDING_VALIDATION_SUPERVISOR',
    Deleted = 'DELETED',
    newOnBeHalf = 'NEW_ON_BEHALF',
    Expired = 'EXPIRED',
    Declined = 'DECLINED',
    DeclinedClosureRequested = 'DECLINED_CLOSURE_REQUESTED',
    DeclinedClosed= 'DECLINED_CLOSED',
    Completed = 'COMPLETED',
    EscalatedPending = 'ESCALATED_PENDING',
    PendingValidationSupplementalApprover = 'PENDING_VALIDATION_SUPPLEMENTAL_APPROVER'

}
