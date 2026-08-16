package sg.breach.user.controller;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import sg.breach.user.entity.ConnectedUser;
import sg.breach.user.entity.Permission;
import sg.breach.user.service.UserService;

import java.util.List;
import java.util.Map;

@RestController
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/me")
    public Map<String, Object> getMe(HttpServletRequest request) {
        ConnectedUser connectedUser = userService.getOneBy(request);
        List<String> roles = connectedUser.roleScopes();
        List<Permission> permissions = connectedUser.permissions();

        return Map.of(
                "name",            (connectedUser.firstName() + " " + connectedUser.lastName()).trim(),
                "email",           connectedUser.email(),
                "firstName",       connectedUser.firstName(),
                "lastName",        connectedUser.lastName(),
                "igg",             connectedUser.igg(),
                "profile",         connectedUser.profile(),
                "roles",           roles,
                "permissions",     permissions,
                "accessiblePages", userService.resolveAccessiblePages(permissions)
        );
    }
}
