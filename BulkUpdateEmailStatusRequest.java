package sg.breach.breachdraft.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public record BulkUpdateEmailStatusRequest(
        @NotEmpty(message = "IDs list cannot be empty") List<Long> ids,
        @NotNull(message = "Email status is required") String emailStatus,
        String updatedBy
) {
}
