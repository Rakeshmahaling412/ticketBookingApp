package sg.breach.breachdraft.dto;

import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

public record BreachDraftFilter(
        String breachCaseId,
        String breachCaseInputter,
        String emailAddress,
        String employeeName,
        String employeeIgg,
        String legalEntity,
        String businessUnit,
        String breachCategory,
        String breachType,
        String suggestedSeverity,
        String breachFrequency,
        String cumulativeBreachScore,
        String status,
        String identificationMethod,
        String emailStatus,
        String batchId,
        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
        LocalDate identifiedBreachDate,
        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
        LocalDate breachDate

) {
}