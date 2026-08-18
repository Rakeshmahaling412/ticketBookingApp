package sg.breach.breachdraft.service;

import java.util.List;
import java.util.Locale;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jspecify.annotations.Nullable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import sg.breach.breachdraft.dto.BreachDraftFilter;
import sg.breach.breachdraft.dto.BreachDraftResponse;
import sg.breach.breachdraft.dto.BreachDraftSpecification;
import sg.breach.breachdraft.dto.CreateBreachDraftRequest;
import sg.breach.breachdraft.dto.SaveDraftToBreachRequest;
import sg.breach.breachdraft.dto.UpdateBreachDraftRequest;
import sg.breach.breachdraft.entity.BreachDraftEntity;
import sg.breach.breachdraft.repository.BreachDraftRepository;
import sg.breach.user.entity.ConnectedUser;
import sg.breach.user.service.UserService;


@Slf4j
@Service
@RequiredArgsConstructor
public class BreachDraftService {

    private static final String DEFAULT_ACTOR = "system";
    private static final String EXPIRED = "EXPIRED";

    private final BreachDraftRepository breachDraftRepository;
    private final UserService  userService;


    @Transactional(readOnly = true)
    public BreachDraftResponse getById(long id) {
        return toResponse(findDraftOrThrow(id));
    }

//    @Transactional(readOnly = true)
//    public Page<BreachDraftResponse> getAll(Pageable pageable, BreachDraftFilter filter) {
//
//        Specification<BreachDraftEntity> specification = BreachDraftSpecification.filter(filter);
//        return breachDraftRepository.findAll(specification, pageable).map(this::toResponse);
//    }

    @Transactional(readOnly = true)
    public Page<BreachDraftResponse> getAll(Pageable pageable,BreachDraftFilter filter,ConnectedUser user) {

        String profileName = userService.resolveProfile(user.permissions());
        String currentIgg = user.igg();

        List<String> readableEntities = user.roleScopes();
        List<String> readableBpos = user.roleScopes();
        log.info("User profile: {}, IGG: {}, Readable Entities: {}, Readable BPOs: {}", profileName, currentIgg, readableEntities, readableBpos);

        Specification<BreachDraftEntity> filterSpec = BreachDraftSpecification.filter(filter);

        Specification<BreachDraftEntity> accessSpec = BreachDraftSpecification.accessControl(profileName, currentIgg, readableEntities, readableBpos);

        return breachDraftRepository.findAll(filterSpec.and(accessSpec), pageable).map(this::toResponse);
    }



    @Transactional
    public BreachDraftResponse create(CreateBreachDraftRequest request, ConnectedUser user) {
        if (request == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Request cannot be null");
        }

        String normalizedEmail = normalizeEmail(request.emailAddress());
        if (!isValidEmail(normalizedEmail)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Email address must be valid");
        }

        String actor = normalizeActor(user.igg());
        BreachDraftEntity entity = new BreachDraftEntity();
        entity.setBatchId(trimToNull(request.batchId()));
        entity.setComplianceOfficer(trimOrDefault(request.complianceOfficer(), ""));
        entity.setEmailAddress(normalizedEmail);
        entity.setEmployeeName(trimToNull(request.employeeName()));
        entity.setEmployeeIgg(trimToNull(request.employeeIgg()));
        entity.setBusinessUnit(trimToNull(request.businessUnit()));
        entity.setLegalEntity(trimToNull(request.legalEntity()));
        entity.setLocation(trimToNull(request.location()));
        entity.setManagerEmailAddress(normalizeEmail(request.managerEmailAddress()));
        entity.setTransversalBreach(trimToNull(request.transversalBreach()));
        entity.setPolicy(trimToNull(request.policy()));
        entity.setBreachType(trimToNull(request.breachType()));
        entity.setDescription(trimToNull(request.description()));
        entity.setIdentifiedBreachDate(request.identifiedBreachDate());
        entity.setBreachDates(request.breachDates());
        entity.setStatus(trimToNull(request.status()));
        entity.setIdentificationMethod(trimToNull(request.identificationMethod()));
        entity.setRootCause(trimToNull(request.rootCause()));
        entity.setLicensedStaff(trimToNull(request.licensedStaff()));
        entity.setRegulatorsNotified(trimToNull(request.regulatorsNotified()));
        entity.setEmailStatus(trimToNull(request.emailStatus()));
        entity.setEmailContent(trimToNull(request.emailContent()));
        entity.setEmailCommentsToStaff(trimToNull(request.emailCommentsToStaff()));
        entity.setComments(trimToNull(request.comments()));
        entity.setReportedToRegulatorDate(request.reportedToRegulatorDate());
        entity.setActionPlanId(trimToNull(request.actionPlanId()));
        entity.setActionPlanShortDescription(trimToNull(request.actionPlanShortDescription()));
        entity.setActionPlanDueDate(request.actionPlanDueDate());
        entity.setActionPlanCompletedDate(request.actionPlanCompletedDate());
        entity.setCommitteeName(trimToNull(request.committeeName()));
        entity.setDateSentToCommittee(request.dateSentToCommittee());
        entity.setSmeConfirmedSeverity(request.smeConfirmedSeverity());
        entity.setSubtypeQaList(request.subtypeQaList());
        entity.setJobTitle(trimToNull(request.jobTitle()));
        entity.setContractType(trimToNull(request.contractType()));
        entity.setPhysicalStartDate(request.physicalStartDate());
        entity.setLocalDepartment(trimOrDefault(request.localDepartment(), ""));
        entity.setEntity(trimToNull(request.entity()));
        entity.setBreachReviewPeriod(trimToNull(request.breachReviewPeriod()));
        entity.setAction(trimToNull(request.action()));
        entity.setT2eorem(trimToNull(request.t2eorem()));
        entity.setEmailSentTimestamp(request.emailSentTimestamp());
        entity.setEmailSentTo(normalizeEmail(request.emailSentTo()));
        entity.setEmailCc(normalizeEmail(request.emailCc()));
        entity.setBreachScore(null);
        entity.setOccurrence(null);
        entity.setCumulativeBreachScore(null);
        entity.setRecommendedAction(null);
        entity.setCreateBy(actor);
        entity.setLastUpdateBy(actor);

        return toResponse(breachDraftRepository.save(entity));
    }


    @Transactional
    public BreachDraftResponse update(long id, UpdateBreachDraftRequest request,ConnectedUser user) {
        BreachDraftEntity entity = findDraftOrThrow(id);

        if (request.batchId() != null) {
            entity.setBatchId(trimToNull(request.batchId()));
        }
        if (request.complianceOfficer() != null) {
            entity.setComplianceOfficer(trimOrDefault(request.complianceOfficer(), ""));
        }
        if (request.emailAddress() != null) {
            String normalizedEmail = normalizeEmail(request.emailAddress());
            if (!isValidEmail(normalizedEmail)) {
                throw new ResponseStatusException(
                        HttpStatus.BAD_REQUEST,
                        "Email address must be valid"
                );
            }
            entity.setEmailAddress(normalizedEmail);
        }
        if (request.employeeName() != null) {
            entity.setEmployeeName(trimToNull(request.employeeName()));
        }
        if (request.employeeIgg() != null) {
            entity.setEmployeeIgg(trimToNull(request.employeeIgg()));
        }
        if (request.businessUnit() != null) {
            entity.setBusinessUnit(trimToNull(request.businessUnit()));
        }
        if (request.legalEntity() != null) {
            entity.setLegalEntity(trimToNull(request.legalEntity()));
        }
        if (request.location() != null) {
            entity.setLocation(trimToNull(request.location()));
        }
        if (request.managerEmailAddress() != null) {
            entity.setManagerEmailAddress(normalizeEmail(request.managerEmailAddress()));
        }
        if (request.transversalBreach() != null) {
            entity.setTransversalBreach(trimToNull(request.transversalBreach()));
        }
        if (request.policy() != null) {
            entity.setPolicy(trimToNull(request.policy()));
        }
        if (request.breachType() != null) {
            entity.setBreachType(trimToNull(request.breachType()));
        }
        if (request.description() != null) {
            entity.setDescription(trimToNull(request.description()));
        }
        if (request.identifiedBreachDate() != null) {
            entity.setIdentifiedBreachDate(request.identifiedBreachDate());
        }
        if (request.breachDates() != null) {
            entity.setBreachDates(request.breachDates());
        }
        if (request.status() != null) {
            entity.setStatus(trimToNull(request.status()));
        }
        if (request.identificationMethod() != null) {
            entity.setIdentificationMethod(trimToNull(request.identificationMethod()));
        }
        if (request.rootCause() != null) {
            entity.setRootCause(trimToNull(request.rootCause()));
        }
        if (request.licensedStaff() != null) {
            entity.setLicensedStaff(trimToNull(request.licensedStaff()));
        }
        if (request.regulatorsNotified() != null) {
            entity.setRegulatorsNotified(trimToNull(request.regulatorsNotified()));
        }
        if (request.emailStatus() != null) {
            entity.setEmailStatus(trimToNull(request.emailStatus()));
        }
        if (request.emailContent() != null) {
            entity.setEmailContent(trimToNull(request.emailContent()));
        }
        if (request.emailCommentsToStaff() != null) {
            entity.setEmailCommentsToStaff(trimToNull(request.emailCommentsToStaff()));
        }
        if (request.comments() != null) {
            entity.setComments(trimToNull(request.comments()));
        }
        if (request.reportedToRegulatorDate() != null) {
            entity.setReportedToRegulatorDate(request.reportedToRegulatorDate());
        }
        if (request.actionPlanId() != null) {
            entity.setActionPlanId(trimToNull(request.actionPlanId()));
        }
        if (request.actionPlanShortDescription() != null) {
            entity.setActionPlanShortDescription(trimToNull(request.actionPlanShortDescription()));
        }
        if (request.actionPlanDueDate() != null) {
            entity.setActionPlanDueDate(request.actionPlanDueDate());
        }
        if (request.actionPlanCompletedDate() != null) {
            entity.setActionPlanCompletedDate(request.actionPlanCompletedDate());
        }
        if (request.committeeName() != null) {
            entity.setCommitteeName(trimToNull(request.committeeName()));
        }
        if (request.dateSentToCommittee() != null) {
            entity.setDateSentToCommittee(request.dateSentToCommittee());
        }
        if (request.smeConfirmedSeverity() != null) {
            entity.setSmeConfirmedSeverity(request.smeConfirmedSeverity());
        }
        if (request.subtypeQaList() != null) {
            entity.setSubtypeQaList(request.subtypeQaList());
        }
        if (request.jobTitle() != null) {
            entity.setJobTitle(trimToNull(request.jobTitle()));
        }
        if (request.contractType() != null) {
            entity.setContractType(trimToNull(request.contractType()));
        }
        if (request.physicalStartDate() != null) {
            entity.setPhysicalStartDate(request.physicalStartDate());
        }
        if (request.localDepartment() != null) {
            entity.setLocalDepartment(trimOrDefault(request.localDepartment(), ""));
        }
        if (request.entity() != null) {
            entity.setEntity(trimToNull(request.entity()));
        }
        if (request.breachReviewPeriod() != null) {
            entity.setBreachReviewPeriod(trimToNull(request.breachReviewPeriod()));
        }
        if (request.action() != null) {
            entity.setAction(trimToNull(request.action()));
        }
        if (request.t2eorem() != null) {
            entity.setT2eorem(trimToNull(request.t2eorem()));
        }
        if (request.emailSentTimestamp() != null) {
            entity.setEmailSentTimestamp(request.emailSentTimestamp());
        }
        if (request.emailSentTo() != null) {
            entity.setEmailSentTo(normalizeEmail(request.emailSentTo()));
        }
        if (request.emailCc() != null) {
            entity.setEmailCc(normalizeEmail(request.emailCc()));
        }

        entity.setLastUpdateBy(normalizeActor(user.firstName()));

        return toResponse(breachDraftRepository.save(entity));
    }


//    @Transactional
//    public BreachDraftResponse saveDraftToBreach(long id, SaveDraftToBreachRequest request, ConnectedUser user) {
//
//        BreachDraftEntity entity = findDraftOrThrow(id);
//        if (request == null) {
//            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Request cannot be null");
//        }
//        if (request.breachScore() != null) {
//            entity.setBreachScore(request.breachScore());
//        }
//        if (request.occurrence() != null) {
//            entity.setOccurrence(request.occurrence());
//        }
//        if (request.cumulativeBreachScore() != null) {
//            entity.setCumulativeBreachScore(request.cumulativeBreachScore());
//        }
//        if (request.recommendedAction() != null) {
//            entity.setRecommendedAction(trimToNull(request.recommendedAction()));
//        }
//        entity.setLastUpdateBy(normalizeActor(user.igg()));
//        return toResponse(breachDraftRepository.save(entity));
//    }
//

    @Transactional
    public void delete(long id) {
        BreachDraftEntity entity = findDraftOrThrow(id);
        breachDraftRepository.delete(entity);
    }




    private BreachDraftEntity findDraftOrThrow(long id) {
        return breachDraftRepository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Breach draft with id '" + id + "' not found"));
    }

    private BreachDraftResponse toResponse(BreachDraftEntity entity) {
        return new BreachDraftResponse(
                entity.getId(),
                entity.getBatchId(),
                entity.getComplianceOfficer(),
                entity.getEmailAddress(),
                entity.getEmployeeName(),
                entity.getEmployeeIgg(),
                entity.getBusinessUnit(),
                entity.getLegalEntity(),
                entity.getLocation(),
                entity.getManagerEmailAddress(),
                entity.getTransversalBreach(),
                entity.getPolicy(),
                entity.getBreachType(),
                entity.getDescription(),
                entity.getIdentifiedBreachDate(),
                entity.getBreachDates(),
                entity.getStatus(),
                entity.getIdentificationMethod(),
                entity.getRootCause(),
                entity.getLicensedStaff(),
                entity.getRegulatorsNotified(),
                entity.getEmailStatus(),
                entity.getEmailContent(),
                entity.getEmailCommentsToStaff(),
                entity.getComments(),
                entity.getReportedToRegulatorDate(),
                entity.getActionPlanId(),
                entity.getActionPlanShortDescription(),
                entity.getActionPlanDueDate(),
                entity.getActionPlanCompletedDate(),
                entity.getCommitteeName(),
                entity.getDateSentToCommittee(),
                entity.getSmeConfirmedSeverity(),
                entity.getBreachScore(),
                entity.getOccurrence(),
                entity.getCumulativeBreachScore(),
                entity.getSubtypeQaList(),
                entity.getJobTitle(),
                entity.getContractType(),
                entity.getPhysicalStartDate(),
                entity.getLocalDepartment(),
                entity.getEntity(),
                entity.getBreachReviewPeriod(),
                entity.getAction(),
                entity.getT2eorem(),
                entity.getEmailSentTimestamp(),
                entity.getEmailSentTo(),
                entity.getEmailCc(),
                entity.getRecommendedAction(),
                entity.getCreateBy(),
                entity.getCreateTime(),
                entity.getLastUpdateBy(),
                entity.getLastUpdateTime()
        );
    }

//
//    @Transactional
//    public void massiveUpdateStatusExpired(List<Long> ids, ConnectedUser user) {
//        if (ids == null || ids.isEmpty()) {
//            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "IDs list cannot be empty");
//        }
//
//        List<BreachDraftEntity> drafts = breachDraftRepository.findAllById(ids);
//
//        if (drafts.isEmpty()) {
//            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No drafts found with provided IDs");
//        }
//
//        String actor = normalizeActor(user.igg());
//        for (BreachDraftEntity draft : drafts) {
//            draft.setStatus(EXPIRED);
//            draft.setLastUpdateBy(actor);
//        }
//        breachDraftRepository.saveAll(drafts);
//    }


    private String normalizeActor(String actor) {
        return hasText(actor) ? actor.trim().toLowerCase(Locale.ROOT) : DEFAULT_ACTOR;
    }

    private @Nullable String normalizeEmail(@Nullable String email) {
        if (!hasText(email)) {
            return null;
        }
        return email.trim().toLowerCase(Locale.ROOT);
    }

    private boolean isValidEmail(@Nullable String email) {
        if (email == null || email.isEmpty()) {
            return false;
        }
        return email.matches("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$");
    }

    private @Nullable String trimToNull(String value) {
        return hasText(value) ? value.trim() : null;
    }

    private String trimOrDefault(String value, String defaultValue) {
        return hasText(value) ? value.trim() : defaultValue;
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

}

