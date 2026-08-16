package sg.breach.user.entity;

public enum Permission {
    SPECIAL,
    MANAGER_SPECIAL,
    READ_EMPLOYEE,
    READ_BREACH,
    EDIT_BREACH,
    CREATE_BREACH,
    EDIT_EMPLOYEE,
    READ_NOTHING,
    READ_SECURITY,
    WRITE_SECURITY;

    public static Permission from(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }

        // Legacy Flask scopes can include constraints, e.g. read-breach-Region:EMEA or read-breach-BPO:CPLE.
        if (value.startsWith("read-employee")) {
            return READ_EMPLOYEE;
        }
        if (value.startsWith("read-breach")) {
            return READ_BREACH;
        }
        if (value.startsWith("edit-breach")) {
            return EDIT_BREACH;
        }
        if (value.startsWith("create-breach")) {
            return CREATE_BREACH;
        }
        if (value.startsWith("edit-employee")) {
            return EDIT_EMPLOYEE;
        }

        return switch (value) {
            case "special" -> SPECIAL;
            case "manager-special" -> MANAGER_SPECIAL;
            case "read-nothing" -> READ_NOTHING;
            case "read-security" -> READ_SECURITY;
            case "write-security" -> WRITE_SECURITY;
            default -> null;
        };
    }
}
