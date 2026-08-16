package sg.breach.user.service;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.server.resource.authentication.BearerTokenAuthentication;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import sg.breach.user.entity.Page;
import sg.breach.user.entity.ConnectedUser;
import sg.breach.user.entity.Permission;
import sg.breach.user.entity.RoleEntity;
import sg.breach.user.entity.UserEntity;
import sg.breach.user.repository.RoleRepository;
import sg.breach.user.repository.UserRepository;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import jakarta.servlet.http.HttpServletRequest;

@Service
public class UserService {

    private static final String AUTHORITY_PREFIX = "api.breach-log-global_";
    private static final String SCOPE_PREFIX = "SCOPE_";

    private static final String PROFILE_ADMINISTRATOR = "Administrator";
    private static final String PROFILE_MANAGER = "Manager";
    private static final String PROFILE_UBPO_EMEA = "Unit Breach Policy Officer";
    private static final String PROFILE_INPUTTER_EMEA = "Breach Case Inputter";
    private static final String PROFILE_STAFF = "Staff";
    private static final String PROFILE_NO_PROFILE = "NO_PROFILE";
    public static final String CONNECTED_USER_ATTRIBUTE = "connectedUser";

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;

    public UserService(UserRepository userRepository, RoleRepository roleRepository) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
    }

    // Pages visible to Unit Breach Policy Officer level (read-employee implies read-breach too)
    private static final List<Page> UBPO_PAGES = List.of(
            Page.BREACH_LIST, Page.BREACH_VIEW, Page.BREACH_CREATE, Page.BREACH_EDIT, Page.BREACH_DELETE,
            Page.BREACH_DRAFT_LIST, Page.BREACH_DRAFT_VIEW, Page.BREACH_DRAFT_CREATE, Page.BREACH_DRAFT_EDIT, Page.BREACH_DRAFT_DELETE,
            Page.EMPLOYEE_LIST, Page.EMPLOYEE_VIEW, Page.EMPLOYEE_EDIT,
            Page.SCORE_LIST, Page.SCORE_VIEW,
            Page.RECOMMENDED_ACTIONS_LIST, Page.RECOMMENDED_ACTIONS_VIEW
    );

    // Pages visible to Breach Case Inputter level (read-breach only)
    private static final List<Page> INPUTTER_PAGES = List.of(
            Page.BREACH_LIST, Page.BREACH_VIEW, Page.BREACH_CREATE, Page.BREACH_EDIT, Page.BREACH_DELETE,
            Page.BREACH_DRAFT_LIST, Page.BREACH_DRAFT_VIEW, Page.BREACH_DRAFT_CREATE, Page.BREACH_DRAFT_EDIT, Page.BREACH_DRAFT_DELETE
    );

    private static final Map<Permission, List<Page>> PERMISSION_PAGE_MAP = Map.of(
            Permission.SPECIAL,          List.of(Page.values()),
            Permission.MANAGER_SPECIAL,  List.of(Page.EMPLOYEE_LIST, Page.EMPLOYEE_VIEW),
            Permission.READ_EMPLOYEE,    UBPO_PAGES,
            Permission.READ_BREACH,      INPUTTER_PAGES,
            Permission.READ_NOTHING,     List.of()
    );

    public List<String> resolveRoleScopes(BearerTokenAuthentication authentication) {
        return authentication.getAuthorities().stream()
                             .map(GrantedAuthority::getAuthority)
                             .map(this::extractScopeName)
                             .filter(Objects::nonNull)
                             .distinct()
                             .collect(Collectors.toList());
    }

    public List<Permission> resolvePermissions(BearerTokenAuthentication authentication) {
        return resolveRoleScopes(authentication).stream()
                             .map(Permission::from)
                             .filter(Objects::nonNull)
                             .distinct()
                             .collect(Collectors.toList());
    }

    public String resolveProfile(List<Permission> permissions) {
        // Priority is intentionally aligned with the legacy Flask logic.
        if (permissions.contains(Permission.SPECIAL)) {
            return PROFILE_ADMINISTRATOR;
        }
        if (permissions.contains(Permission.MANAGER_SPECIAL)) {
            return PROFILE_MANAGER;
        }
        if (permissions.contains(Permission.READ_EMPLOYEE)) {
            return PROFILE_UBPO_EMEA;
        }
        if (permissions.contains(Permission.READ_BREACH)) {
            return PROFILE_INPUTTER_EMEA;
        }
        if (permissions.contains(Permission.READ_NOTHING)) {
            return PROFILE_STAFF;
        }
        return PROFILE_NO_PROFILE;
    }

    public List<String> resolveAccessiblePages(List<Permission> permissions) {
        return permissions.stream()
                          .flatMap(p -> PERMISSION_PAGE_MAP.getOrDefault(p, List.of()).stream())
                          .distinct()
                          .map(Page::name)
                          .collect(Collectors.toList());
    }

    public ConnectedUser buildAndPersistConnectedUser(BearerTokenAuthentication authentication) {
        String email = readStringClaim(authentication, "mail", "email");
        String firstName = readStringClaim(authentication, "first_name", "firstName");
        String lastName = readStringClaim(authentication, "last_name", "lastName");
        String igg = readStringClaim(authentication, "igg");
        String department = readStringClaim(authentication, "rc_local_sigle", "department");

        List<String> roleScopes = resolveRoleScopes(authentication);
        List<Permission> permissions = resolvePermissions(authentication);

        UserEntity user = userRepository.findOneByEmailIgnoreCase(email)
                .orElseGet(UserEntity::new);

        user.setEmail(email.toLowerCase());
        user.setFirstName(firstName);
        user.setLastName(lastName);
        user.setIgg(igg);
        user.setDepartment(department);
        user.setActive(true);
        user.setLoginCount(user.getLoginCount() == null ? 1 : user.getLoginCount() + 1);

        if (!Boolean.TRUE.equals(user.getFrozenRoles())) {
            Set<String> scopeNames = new HashSet<>(roleScopes);
            Set<RoleEntity> scopedRoles = new HashSet<>(roleRepository.findByNameIn(scopeNames));
            user.setRoles(scopedRoles);
        }

        userRepository.save(user);

        return new ConnectedUser(
                email,
                firstName,
                lastName,
                igg,
                department,
                roleScopes,
                permissions,
                resolveProfile(permissions)
        );
    }

    public ConnectedUser getOneBy(HttpServletRequest request) {
        Object raw = request.getAttribute(CONNECTED_USER_ATTRIBUTE);
        if (raw instanceof ConnectedUser connectedUser) {
            return connectedUser;
        }
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Unauthorized");
    }

    private String extractScopeName(String authority) {
        if (authority == null || authority.isBlank()) {
            return null;
        }

        String normalized = authority.startsWith(SCOPE_PREFIX)
                ? authority.substring(SCOPE_PREFIX.length())
                : authority;

        if (!normalized.startsWith(AUTHORITY_PREFIX)) {
            return null;
        }

        return normalized.substring(AUTHORITY_PREFIX.length());
    }

    private String readStringClaim(BearerTokenAuthentication authentication, String... claimNames) {
        for (String claimName : claimNames) {
            Object raw = authentication.getTokenAttributes().get(claimName);
            if (raw == null) {
                continue;
            }
            String value = String.valueOf(raw).trim();
            if (!value.isEmpty()) {
                return value;
            }
        }
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Missing required token claims");
    }
}