package sg.breach.breachdraft.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;

import java.util.Arrays;
import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import sg.breach.breachdraft.dto.BreachDraftFilter;
import sg.breach.breachdraft.dto.BreachDraftResponse;
import sg.breach.breachdraft.dto.CreateBreachDraftRequest;
import sg.breach.breachdraft.dto.UpdateBreachDraftRequest;
import sg.breach.breachdraft.service.BreachDraftService;
import sg.breach.user.entity.ConnectedUser;
import sg.breach.user.entity.Permission;
import sg.breach.user.service.UserService;

@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/breach-drafts")
public class BreachDraftsController {

    private final BreachDraftService breachDraftService;
    private final UserService userService;


    @GetMapping("/{id}")
    public BreachDraftResponse getById(@PathVariable long id, HttpServletRequest request) {
        ConnectedUser user = getAuthenticatedUser(request);
        checkAnyPermission(
                user,
                Permission.CREATE_BREACH,
                Permission.SPECIAL
        );
        return breachDraftService.getById(id);
    }


    @GetMapping
    public Page<BreachDraftResponse> getAll(
            BreachDraftFilter filter,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size,
            HttpServletRequest httpRequest) {
        ConnectedUser user = getAuthenticatedUser(httpRequest);

//        String profileName = userService.resolveProfile(user.permissions());
//
//        String currentIgg = currentUser.getIgg();
//
//        List<String> readableEntities = getUserBreachReadableEntities();
//        List<String> readableBpos     = getUserBreachReadableBpos();
//
////        checkPermission(user, Permission.READ_BREACH);
//        checkAnyPermission(
//                user,
//                Permission.CREATE_BREACH,
//                Permission.SPECIAL
//        );
        Pageable pageable = PageRequest.of(page, size);

        return breachDraftService.getAll(pageable, filter,user);
    }




//    @GetMapping
//    public Page<BreachDraftResponse> getAll(@RequestParam(defaultValue = "0") int page, @RequestParam(defaultValue = "50") int size,
//                                            @RequestParam(required = false) String breachCaseId,
//                                            @RequestParam(required = false) String breachCaseInputter,
//                                            @RequestParam(required = false) String emailAddress,
//                                            @RequestParam(required = false) String employeeName,
//                                            @RequestParam(required = false) String employeeIgg,
//                                            @RequestParam(required = false) String legalEntity,
//                                            @RequestParam(required = false) String businessUnit,
//                                            @RequestParam(required = false) String breachCategory,
//                                            @RequestParam(required = false) String breachType,
//                                            @RequestParam(required = false) String suggestedSeverity,
//                                            @RequestParam(required = false) String breachFrequency,
//                                            @RequestParam(required = false) String cumulativeBreachScore,
//                                            @RequestParam(required = false) String identifiedBreachDate,
//                                            @RequestParam(required = false) String breachDate,
//                                            @RequestParam(required = false) String status,
//                                            @RequestParam(required = false) String identificationMethod,
//                                            @RequestParam(required = false) String emailStatus,
//                                            @RequestParam(required = false) String batchId,
//                                            HttpServletRequest httpRequest) {
//
//        ConnectedUser user = getAuthenticatedUser(httpRequest);
////        checkPermission(user, Permission.READ_BREACH);
//        checkAnyPermission(
//                user,
//                Permission.CREATE_BREACH,
//                Permission.SPECIAL
//        );
//        Pageable pageable = PageRequest.of(page, size);
//        return breachDraftService.getAll(pageable, f);
//    }


//    @GetMapping("/by-creator/{creator}")
//    public List<BreachDraftResponse> getByCreator(@PathVariable String creator , HttpServletRequest request) {
//        ConnectedUser user = getAuthenticatedUser(request);
//        checkPermission(user, Permission.READ_BREACH);
//        return breachDraftService.getByCreator(creator);
//    }

//    @GetMapping("/by-entities")
//    public List<BreachDraftResponse> getByLegalEntities(@RequestParam List<String> entities, HttpServletRequest request) {
//        ConnectedUser user = getAuthenticatedUser(request);
//        checkPermission(user, Permission.READ_BREACH);
//        return breachDraftService.getByLegalEntities(entities);
//    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public BreachDraftResponse create(@Valid @RequestBody CreateBreachDraftRequest DraftRequest,HttpServletRequest httpRequest) {
        ConnectedUser user = getAuthenticatedUser(httpRequest);
        checkAnyPermission(user, Permission.CREATE_BREACH, Permission.SPECIAL
        );
        return breachDraftService.create(DraftRequest,user);
    }

    @PutMapping("/{id}")
    public BreachDraftResponse update(@PathVariable Long id, @RequestBody UpdateBreachDraftRequest request, HttpServletRequest httpRequest) {
        ConnectedUser user = getAuthenticatedUser(httpRequest);
//        checkPermission(user, Permission.EDIT_BREACH);
        checkAnyPermission(
                user,
                Permission.EDIT_BREACH,
                Permission.SPECIAL
        );
        return breachDraftService.update(id, request,user);
    }

    @PatchMapping("/{id}")
    public BreachDraftResponse patch(@PathVariable Long id,
            @RequestBody UpdateBreachDraftRequest request,
            HttpServletRequest httpRequest) {
        ConnectedUser user = getAuthenticatedUser(httpRequest);
        checkAnyPermission(user, Permission.EDIT_BREACH, Permission.SPECIAL
        );
        return breachDraftService.update(id, request, user);
    }

//    @PostMapping("/{id}/save-to-breach")
//    public BreachDraftResponse saveDraftToBreach(@PathVariable long id, @Valid @RequestBody SaveDraftToBreachRequest request, HttpServletRequest httpRequest) {
//        ConnectedUser user = getAuthenticatedUser(httpRequest);
//        checkPermission(user, Permission.EDIT_BREACH);
//        return breachDraftService.saveDraftToBreach(id, request,user);
//    }


    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable long id,HttpServletRequest httpRequest) {
        ConnectedUser user = getAuthenticatedUser(httpRequest);
//        checkPermission(user, Permission.EDIT_BREACH);
        checkAnyPermission(
                user,
                Permission.EDIT_BREACH,
                Permission.SPECIAL
        );
        breachDraftService.delete(id);
    }




//    @PostMapping("/status/expired")
//    public ResponseEntity<Void> massiveUpdateStatusExpired(
//            @RequestBody List<Long> ids,
//            @AuthenticationPrincipal ConnectedUser user) {
//        breachDraftService.massiveUpdateStatusExpired(ids, user);
//        return ResponseEntity.noContent().build();
//    }

    private ConnectedUser getAuthenticatedUser(HttpServletRequest request) {
        return userService.getOneBy(request);
    }

    private void checkPermission(ConnectedUser user, Permission requiredPermission) {
        if (user == null || user.permissions() == null || !user.permissions().contains(requiredPermission)) {
            throw new org.springframework.web.server.ResponseStatusException(HttpStatus.FORBIDDEN, "User does not have required permission");
        }
    }

    private void checkAnyPermission(ConnectedUser user, Permission... requiredPermissions) {
        if (user == null || user.permissions() == null
            || Arrays.stream(requiredPermissions)
                     .noneMatch(user.permissions()::contains)) {
            throw new ResponseStatusException(
                    HttpStatus.UNAUTHORIZED,
                    "User does not have required permission"
            );
        }
    }
}
