package sg.breach.breachdraft.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.validation.constraints.Email;
import java.time.LocalDate;
import java.time.LocalDateTime;

public record UpdateBreachDraftRequest(
        String batchId,
        String complianceOfficer,
        @Email(message = "Email address must be valid") String emailAddress,
        String employeeName,
        String employeeIgg,
        String businessUnit,
        String legalEntity,
        String location,
        String managerEmailAddress,
        String transversalBreach,
        String policy,
        String breachType,
        String description,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate identifiedBreachDate,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate[] breachDates,
        String status,
        String identificationMethod,
        String rootCause,
        String licensedStaff,
        String regulatorsNotified,
        String emailStatus,
        String emailContent,
        String emailCommentsToStaff,
        String comments,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate reportedToRegulatorDate,
        String actionPlanId,
        String actionPlanShortDescription,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate actionPlanDueDate,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate actionPlanCompletedDate,
        String committeeName,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate dateSentToCommittee,
        Integer smeConfirmedSeverity,
        String[] subtypeQaList,
        String jobTitle,
        String contractType,
        @JsonFormat(pattern = "yyyy-MM-dd") LocalDate physicalStartDate,
        String localDepartment,
        String entity,
        String breachReviewPeriod,
        String action,
        String t2eorem,
        LocalDateTime emailSentTimestamp,
        String emailSentTo,
        String emailCc,
        String updatedBy
) {
}


