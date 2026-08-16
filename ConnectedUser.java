package sg.breach.user.entity;

import java.util.List;

public record ConnectedUser(
        String email,
        String firstName,
        String lastName,
        String igg,
        String department,
        List<String> roleScopes,
        List<Permission> permissions,
        String profile
) {
}
