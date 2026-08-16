package sg.breach.user.entity;

public enum Page {
    BREACH_LIST("breach", "LIST"),
    BREACH_CREATE("breach", "CREATE"),
    BREACH_VIEW("breach", "VIEW"),
    BREACH_EDIT("breach", "EDIT"),
    BREACH_DELETE("breach", "DELETE"),
    BREACH_DRAFT_LIST("breachDrafts", "LIST"),
    BREACH_DRAFT_CREATE("breachDrafts", "CREATE"),
    BREACH_DRAFT_VIEW("breachDrafts", "VIEW"),
    BREACH_DRAFT_EDIT("breachDrafts", "EDIT"),
    BREACH_DRAFT_DELETE("breachDrafts", "DELETE"),
    EMPLOYEE_LIST("employee", "LIST"),
    EMPLOYEE_VIEW("employee", "VIEW"),
    EMPLOYEE_EDIT("employee", "EDIT"),
    SCORE_LIST("score", "LIST"),
    SCORE_CREATE("score", "CREATE"),
    SCORE_VIEW("score", "VIEW"),
    SCORE_EDIT("score", "EDIT"),
    SCORE_DELETE("score", "DELETE"),
    EMAIL_BLACKLIST_LIST("emailBlacklist", "LIST"),
    EMAIL_BLACKLIST_CREATE("emailBlacklist", "CREATE"),
    EMAIL_BLACKLIST_VIEW("emailBlacklist", "VIEW"),
    EMAIL_BLACKLIST_EDIT("emailBlacklist", "EDIT"),
    EMAIL_BLACKLIST_DELETE("emailBlacklist", "DELETE"),
    RECOMMENDED_ACTIONS_LIST("recommendedActions", "LIST"),
    RECOMMENDED_ACTIONS_CREATE("recommendedActions", "CREATE"),
    RECOMMENDED_ACTIONS_VIEW("recommendedActions", "VIEW"),
    RECOMMENDED_ACTIONS_EDIT("recommendedActions", "EDIT"),
    RECOMMENDED_ACTIONS_DELETE("recommendedActions", "DELETE");

    public final String module;
    public final String tab;

    Page(String module, String tab) {
        this.module = module;
        this.tab = tab;
    }
}