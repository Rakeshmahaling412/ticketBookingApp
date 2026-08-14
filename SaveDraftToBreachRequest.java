package sg.breach.breachdraft.dto;

import jakarta.validation.constraints.NotNull;

public record SaveDraftToBreachRequest(
        @NotNull(message = "Draft ID is required") Long draftId,
        Integer breachScore,
        Integer occurrence,
        Integer cumulativeBreachScore,
        String recommendedAction,
        String updatedBy
) {
}
