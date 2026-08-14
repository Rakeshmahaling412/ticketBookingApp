package sg.breach.breachdraft.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Getter
@Setter
@Entity
@Table(name = "breach_drafts")
public class BreachDraftEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "batch_id")
    private String batchId;

    @Column(name = "compliance_officer", nullable = false)
    private String complianceOfficer;

    @Column(name = "email_address", nullable = false)
    private String emailAddress;

    @Column(name = "employee_name")
    private String employeeName;

    @Column(name = "employee_igg")
    private String employeeIgg;

    @Column(name = "business_unit")
    private String businessUnit;

    @Column(name = "legal_entity")
    private String legalEntity;

    @Column(name = "location")
    private String location;

    @Column(name = "manager_email_address")
    private String managerEmailAddress;

    @Column(name = "transversal_breach")
    private String transversalBreach;

    @Column(name = "policy")
    private String policy;

    @Column(name = "breach_type")
    private String breachType;


    @Column(name = "description", columnDefinition = "CLOB")
    private String description;

    @Column(name = "identified_breach_date")
    private LocalDate identifiedBreachDate;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "breach_dates")
    private LocalDate[] breachDates;

    @Column(name = "status")
    private String status;

    @Column(name = "identification_method")
    private String identificationMethod;

    @Column(name = "root_cause")
    private String rootCause;

    @Column(name = "licensed_staff")
    private String licensedStaff;

    @Column(name = "regulators_notified")
    private String regulatorsNotified;

    @Column(name = "email_status")
    private String emailStatus;

    @Column(name = "email_content", columnDefinition = "CLOB")
    private String emailContent;

    @Column(name = "email_comments_to_staff", columnDefinition = "CLOB")
    private String emailCommentsToStaff;

    @Column(name = "comments", columnDefinition = "CLOB")
    private String comments;

    @Column(name = "reported_to_regulator_date")
    private LocalDate reportedToRegulatorDate;

    @Column(name = "action_plan_id")
    private String actionPlanId;

    @Column(name = "action_plan_short_description")
    private String actionPlanShortDescription;

    @Column(name = "action_plan_due_date")
    private LocalDate actionPlanDueDate;

    @Column(name = "action_plan_completed_date")
    private LocalDate actionPlanCompletedDate;

    @Column(name = "committee_name")
    private String committeeName;

    @Column(name = "date_sent_to_committee")
    private LocalDate dateSentToCommittee;

    @Column(name = "sme_confirmed_severity")
    private Integer smeConfirmedSeverity;

    @Column(name = "breach_score")
    private Integer breachScore;

    @Column(name = "occurrence")
    private Integer occurrence;

    @Column(name = "cumulative_breach_score")
    private Integer cumulativeBreachScore;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "subtype_qa_list")
    private String[] subtypeQaList;

    @Column(name = "job_title")
    private String jobTitle;

    @Column(name = "contract_type")
    private String contractType;

    @Column(name = "physical_start_date")
    private LocalDate physicalStartDate;

    @Column(name = "local_department", nullable = false)
    private String localDepartment;

    @Column(name = "entity")
    private String entity;

    @Column(name = "breach_review_period")
    private String breachReviewPeriod;

    @Column(name = "action")
    private String action;

    @Column(name = "t2eorem")
    private String t2eorem;

    @Column(name = "email_sent_timestamp")
    private LocalDateTime emailSentTimestamp;

    @Column(name = "email_sent_to")
    private String emailSentTo;

    @Column(name = "email_cc")
    private String emailCc;

    @Column(name = "recommended_action")
    private String recommendedAction;

    @Column(name = "create_by", nullable = false)
    private String createBy;

    @CreationTimestamp
    @Column(name = "create_time", nullable = false, updatable = false)
    private LocalDateTime createTime;

    @Column(name = "last_update_by", nullable = false)
    private String lastUpdateBy;

    @UpdateTimestamp
    @Column(name = "last_update_time", nullable = false)
    private LocalDateTime lastUpdateTime;
}


