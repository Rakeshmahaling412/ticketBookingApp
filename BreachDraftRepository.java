package sg.breach.breachdraft.repository;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import sg.breach.breachdraft.entity.BreachDraftEntity;


public interface BreachDraftRepository extends JpaRepository<BreachDraftEntity, Long> {

    List<BreachDraftEntity> findByCreateByOrderByCreateTimeDesc(String createBy);

    List<BreachDraftEntity> findByLegalEntityInOrderByCreateTimeDesc(List<String> legalEntities);

    @Query("SELECT DISTINCT bd.emailStatus FROM BreachDraftEntity bd WHERE bd.emailStatus IS NOT NULL ORDER BY bd.emailStatus")
    List<String> findDistinctEmailStatuses();

    @Query("SELECT DISTINCT bd.status FROM BreachDraftEntity bd WHERE bd.status IS NOT NULL ORDER BY bd.status")
    List<String> findDistinctStatuses();

    @Query("SELECT DISTINCT bd.identificationMethod FROM BreachDraftEntity bd WHERE bd.identificationMethod IS NOT NULL ORDER BY bd.identificationMethod")
    List<String> findDistinctIdentificationMethods();

    @Query("SELECT DISTINCT bd.breachType FROM BreachDraftEntity bd WHERE bd.breachType IS NOT NULL ORDER BY bd.breachType")
    List<String> findDistinctBreachTypes();

    @Query("SELECT DISTINCT bd.emailAddress FROM BreachDraftEntity bd WHERE bd.emailAddress IS NOT NULL ORDER BY bd.emailAddress")
    List<String> findDistinctEmailAddresses();

    @Query("SELECT DISTINCT bd.policy FROM BreachDraftEntity bd WHERE bd.policy IS NOT NULL ORDER BY bd.policy")
    List<String> findDistinctPolicies();

    @Query("SELECT DISTINCT bd.legalEntity FROM BreachDraftEntity bd WHERE bd.legalEntity IS NOT NULL ORDER BY bd.legalEntity")
    List<String> findDistinctLegalEntities();

    @Query("SELECT DISTINCT bd.businessUnit FROM BreachDraftEntity bd WHERE bd.businessUnit IS NOT NULL ORDER BY bd.businessUnit")
    List<String> findDistinctBusinessUnits();
}


