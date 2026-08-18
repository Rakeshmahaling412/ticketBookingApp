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
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.LinkedHashSet;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class UserService {

    private static final Logger logger = LoggerFactory.getLogger(UserService.class);

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
        Set<String> scopes = new LinkedHashSet<>();

        // 1. Extract base scopes from authorities
        authentication.getAuthorities().stream()
                      .peek(auth -> logger.debug("Processing authority: {}", auth.getAuthority()))
                      .map(GrantedAuthority::getAuthority)
                      .map(this::extractScopeName)
                      .peek(scope -> logger.debug("  -> Extracted scope: {}", scope))
                      .filter(Objects::nonNull)
                      .distinct()
                      .forEach(scopes::add);

        // 2. Extract constrained scopes from user_authorization claim
        List<String> constrainedScopes = extractConstrainedScopes(authentication);
        logger.debug("Extracted constrained scopes: {}", constrainedScopes);
        scopes.addAll(constrainedScopes);

        return scopes.stream().collect(Collectors.toList());
    }

    private List<String> extractConstrainedScopes(BearerTokenAuthentication authentication) {
        List<String> constrainedScopes = new ArrayList<>();

        Object userAuthzRaw = authentication.getTokenAttributes().get("user_authorization");
        if (userAuthzRaw == null) {
            logger.debug("user_authorization claim not found");
            return constrainedScopes;
        }

        logger.debug("user_authorization type = {}", userAuthzRaw.getClass().getName());
        logger.debug("user_authorization raw = {}", userAuthzRaw);

        try {
            ObjectMapper mapper = new ObjectMapper();

            // Handle both cases: already parsed as List or as raw JSON string
            List<?> userAuthzList;
            if (userAuthzRaw instanceof String) {
                userAuthzList = mapper.readValue((String) userAuthzRaw, List.class);
                logger.debug("Parsed user_authorization from JSON string");
            } else if (userAuthzRaw instanceof List) {
                userAuthzList = (List<?>) userAuthzRaw;
                logger.debug("user_authorization already a List");
            } else {
                userAuthzList = mapper.convertValue(userAuthzRaw, List.class);
                logger.debug("Converted user_authorization to List");
            }

            logger.debug("userAuthzList size = {}", userAuthzList.size());

            for (int i = 0; i < userAuthzList.size(); i++) {
                Object authzObj = userAuthzList.get(i);
                logger.debug("Processing authz item {}, type = {}", i, authzObj.getClass().getName());

                Map<?, ?> authz = mapper.convertValue(authzObj, Map.class);
                List<?> permissionsList = (List<?>) authz.get("permissions");

                logger.debug("Permissions list size = {}", (permissionsList != null ? permissionsList.size() : "null"));
                if (permissionsList == null) continue;

                for (int j = 0; j < permissionsList.size(); j++) {
                    Object permObj = permissionsList.get(j);
                    Map<?, ?> perm = mapper.convertValue(permObj, Map.class);
                    String permissionName = (String) perm.get("name");
                    List<?> constraintsList = (List<?>) perm.get("constraints");

                    logger.debug("Permission {}: {}, constraints size = {}", j, permissionName, (constraintsList != null ? constraintsList.size() : "null"));

                    if (constraintsList == null) continue;

                    // Extract constraints for this permission
                    for (int k = 0; k < constraintsList.size(); k++) {
                        Object constraintObj = constraintsList.get(k);
                        Map<?, ?> constraint = mapper.convertValue(constraintObj, Map.class);
                        String constraintName = (String) constraint.get("name");
                        List<?> valuesList = (List<?>) constraint.get("values");

                        logger.debug("Constraint {}: {}, values size = {}", k, constraintName, (valuesList != null ? valuesList.size() : "null"));

                        if (valuesList == null || valuesList.isEmpty()) continue;

                        // Map constraint name to scope suffix
                        for (Object valueObj : valuesList) {
                            String value = (String) valueObj;
                            String scopeConstraint = buildConstrainedScope(permissionName, constraintName, value);
                            if (scopeConstraint != null) {
                                constrainedScopes.add(scopeConstraint);
                                logger.debug("Added constrained scope: {}", scopeConstraint);
                            }
                        }
                    }
                }
            }
            logger.debug("Total constrained scopes extracted: {}", constrainedScopes.size());
        } catch (Exception e) {
            logger.error("Error parsing user_authorization: {}", e.getMessage(), e);
        }

        return constrainedScopes;
    }

    private String buildConstrainedScope(String permission, String constraintName, String value) {
        // Map constraint names to scope format
        // "Business Process Owner (EMEA)" → read-breach-BPO:VALUE
        // "SG legal entities (For GBIS)" → read-breach-VALUE
        // "BU/SU" → read-breach-VALUE (or BPO)

        if (value == null || value.trim().isEmpty()) {
            return null;
        }

        value = value.trim(); // Preserve spaces and special characters

        switch (constraintName) {
            case "Business Process Owner (EMEA)":
                return permission + "-BPO:" + value;
            case "SG legal entities (For GBIS)":
                return permission + "-" + value;
            case "BU/SU":
                // For BU/SU, treat as entities (can add prefix if different behavior needed)
                return permission + "-" + value;
            default:
                return null;
        }
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
        logger.debug("Building connected user from token");
        logger.debug("Authorities: {}", authentication.getAuthorities());

        String email = readRequiredStringClaim(authentication, "mail", "email");
        String firstName = readOptionalStringClaim(authentication, "first_name", "firstName");
        String lastName = readOptionalStringClaim(authentication, "last_name", "lastName");
        String igg = readOptionalStringClaim(authentication, "igg");
        String department = readOptionalStringClaim(authentication, "rc_local_sigle", "department");

        List<String> roleScopes = resolveRoleScopes(authentication);
        logger.debug("Resolved {} roleScopes", roleScopes.size());
        roleScopes.forEach(scope -> logger.debug("  - {}", scope));

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
            logger.debug("    Skipping (doesn't start with {}): {}", AUTHORITY_PREFIX, normalized);
            return null;
        }

        String result = normalized.substring(AUTHORITY_PREFIX.length());
        logger.debug("    Extracted: {}", result);
        return result;
    }

    private String readOptionalStringClaim(BearerTokenAuthentication authentication, String... claimNames) {
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
        return "";
    }

    private String readRequiredStringClaim(BearerTokenAuthentication authentication, String... claimNames) {
        String value = readOptionalStringClaim(authentication, claimNames);
        if (!value.isEmpty()) {
            return value;
        }
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Missing required token claims");
    }
}