package sg.breach.breachdrfat.dto;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.test.context.ActiveProfiles;
import sg.breach.breachdraft.dto.BreachDraftSpecification;
import sg.breach.breachdraft.entity.BreachDraftEntity;
import sg.breach.breachdraft.repository.BreachDraftRepository;
import sg.breach.user.dto.UserAccessContext;
import sg.breach.user.entity.DataAccessScope;

@DataJpaTest
@ActiveProfiles("test")
@DisplayName("BreachDraftSpecification access control - Integration Tests")
class BreachDraftSpecificationAccessControlTest {

    @Autowired
    private BreachDraftRepository breachDraftRepository;

    @Test
    @DisplayName("ALL scope should return every record")
    void testAdministratorSeesEverything() {
        seedDrafts();

        List<BreachDraftEntity> result = breachDraftRepository.findAll(BreachDraftSpecification.accessControl(context(DataAccessScope.ALL, "IGG_OTHER", List.of(), List.of())));

        assertThat(result).hasSize(3);
    }

    @Test
    @DisplayName("OWN scope should return only records created by the user")
    void testInputterSeesOnlyOwnRecords() {
        seedDrafts();

        List<BreachDraftEntity> result = breachDraftRepository.findAll(
                BreachDraftSpecification.accessControl(
                        context(DataAccessScope.OWN, "IGG_OWNER", List.of("CPLE"), List.of("BU"))));

        assertThat(result).hasSize(1);
        assertThat(result.get(0).getCreateBy()).isEqualTo("IGG_OWNER");
    }

    @Test
    @DisplayName("ENTITY_AND_BPO_OR_OWN scope should return matching entity/BPO records plus own records")
    void testUbpoSeesEntityBpoAndOwnRecords() {
        seedDrafts();

        List<BreachDraftEntity> result = breachDraftRepository.findAll(
                BreachDraftSpecification.accessControl(
                        context(DataAccessScope.ENTITY_AND_BPO_OR_OWN, "IGG_OWNER", List.of("CPLE"), List.of("BU1"))));

        assertThat(result)
                .extracting(BreachDraftEntity::getEmailAddress)
                .containsExactlyInAnyOrder("own@test.com", "entity-match@test.com");
    }

    @Test
    @DisplayName("ENTITY_AND_BPO_OR_OWN scope should fall back to own records when no entity/BPO constraint exists")
    void testUbpoWithoutConstraintsFallsBackToOwnRecords() {
        seedDrafts();

        List<BreachDraftEntity> noEntities = breachDraftRepository.findAll(
                BreachDraftSpecification.accessControl(
                        context(DataAccessScope.ENTITY_AND_BPO_OR_OWN, "IGG_OWNER", List.of(), List.of("BU1"))));
        List<BreachDraftEntity> noBpos = breachDraftRepository.findAll(
                BreachDraftSpecification.accessControl(
                        context(DataAccessScope.ENTITY_AND_BPO_OR_OWN, "IGG_OWNER", List.of("CPLE"), List.of())));

        assertThat(noEntities).hasSize(1);
        assertThat(noEntities.get(0).getCreateBy()).isEqualTo("IGG_OWNER");
        assertThat(noBpos).hasSize(1);
        assertThat(noBpos.get(0).getCreateBy()).isEqualTo("IGG_OWNER");
    }

    @Test
    @DisplayName("null access context should return no records")
    void testNullContextDeniesEverything() {
        seedDrafts();

        Specification<BreachDraftEntity> specification = BreachDraftSpecification.accessControl(null);

        assertThat(breachDraftRepository.findAll(specification)).isEmpty();
    }

    private UserAccessContext context(DataAccessScope scope, String igg,
                                      List<String> entities, List<String> bpos) {
        return new UserAccessContext("profile", igg, scope, entities, bpos, scope != DataAccessScope.ALL);
    }

    private void seedDrafts() {
        breachDraftRepository.saveAll(List.of(
                draft("IGG_OWNER", "own@test.com", "CSG", "OTHER"),
                draft("IGG_OTHER", "entity-match@test.com", "CPLE", "BU1-SUB"),
                draft("IGG_OTHER", "no-match@test.com", "CSG", "BU9")
        ));
    }

    private BreachDraftEntity draft(String createBy, String email, String legalEntity, String businessUnit) {
        BreachDraftEntity entity = new BreachDraftEntity();
        entity.setCreateBy(createBy);
        entity.setLastUpdateBy(createBy);
        entity.setComplianceOfficer("Officer");
        entity.setEmailAddress(email);
        entity.setEmployeeName("Employee");
        entity.setEmployeeIgg(createBy);
        entity.setLegalEntity(legalEntity);
        entity.setBusinessUnit(businessUnit);
        entity.setPolicy("POL");
        entity.setBreachType("Type");
        entity.setStatus("Draft");
        entity.setLocalDepartment("Department");
        entity.setIdentifiedBreachDate(LocalDate.of(2026, 8, 1));
        return entity;
    }
}

