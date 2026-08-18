package sg.breach.breachdraft.dto;

import jakarta.persistence.criteria.Predicate;
import org.springframework.data.jpa.domain.Specification;
import sg.breach.breachdraft.entity.BreachDraftEntity;

import java.util.List;

public final class BreachDraftSpecification {
    private static final String PROFILE_ADMINISTRATOR = "Administrator";
    private static final String PROFILE_MANAGER = "Manager";
    private static final String PROFILE_UBPO_EMEA = "Unit Breach Policy Officer";
    private static final String PROFILE_INPUTTER_EMEA = "Breach Case Inputter";
    private static final String PROFILE_STAFF = "Staff";
    private static final String PROFILE_NO_PROFILE = "NO_PROFILE";
    public static final String CONNECTED_USER_ATTRIBUTE = "connectedUser";

    private BreachDraftSpecification() {

    }

    public static Specification<BreachDraftEntity> filter(
            BreachDraftFilter filter) {

        return (root, query, cb) -> {

            Predicate predicate = cb.conjunction();

            if (filter.breachCaseId() != null &&
                !filter.breachCaseId().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("breachCaseId"),
                                 filter.breachCaseId()));
            }

            if (filter.breachCaseInputter() != null &&
                !filter.breachCaseInputter().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("breachCaseInputter"),
                                 filter.breachCaseInputter()));
            }

            if (filter.emailAddress() != null &&
                !filter.emailAddress().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("emailAddress"),
                                 filter.emailAddress()));
            }

            if (filter.employeeName() != null &&
                !filter.employeeName().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.like(
                                cb.lower(root.get("employeeName")),
                                "%" + filter.employeeName().toLowerCase() + "%"
                        ));
            }

            if (filter.legalEntity() != null &&
                !filter.legalEntity().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("legalEntity"),
                                 filter.legalEntity()));
            }

            if (filter.businessUnit() != null &&
                !filter.businessUnit().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("businessUnit"),
                                 filter.businessUnit()));
            }

            if (filter.breachCategory() != null &&
                !filter.breachCategory().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("breachCategory"),
                                 filter.breachCategory()));
            }

            if (filter.breachType() != null &&
                !filter.breachType().isBlank()) {

                predicate = cb.and(
                        predicate,
                        cb.equal(root.get("breachType"),
                                 filter.breachType()));
            }

            return predicate;
        };
    }


    public static Specification<BreachDraftEntity> accessControl(String profileName, String currentIgg, List<String> readableEntities, List<String> readableBpos) {

        return (root, query, cb) -> {
            if (PROFILE_ADMINISTRATOR.equals(profileName)) {
                return cb.conjunction();
            }
            // Inputter -> own records only
            if (PROFILE_INPUTTER_EMEA.equals(profileName)) {
                return cb.equal(root.get("createBy"), currentIgg);
            }
            // BPO
            if (PROFILE_UBPO_EMEA.equals(profileName)) {
                Predicate ownRecords = cb.equal(root.get("createBy"), currentIgg);
                Predicate entityPredicate = root.get("legalEntity").in(readableEntities);
                Predicate businessUnitPredicate = cb.disjunction();
                for (String bu : readableBpos) {
                    businessUnitPredicate = cb.or(businessUnitPredicate, cb.like(root.get("businessUnit"), bu + "%"));
                }
                Predicate bpoAccess = cb.and(entityPredicate, businessUnitPredicate);
                return cb.or(bpoAccess, ownRecords);
            }

            return cb.equal(root.get("createBy"), currentIgg);
        };
    }

    }

 