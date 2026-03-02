package com.socgen.pad.obi.web.constants;

import lombok.experimental.UtilityClass;

@UtilityClass
public final class ActionConstants {
    // Filter types
    public static final String FILTER_SELF_TODO = "self-todo";
    public static final String FILTER_HISTORY = "history";

    // Workflow types
    public static final String WORKFLOW_TYPE_CLOSE = "close";
    public static final String WORKFLOW_TYPE_REGULAR = "regular";

    // Delete types
    public static final String DELETE_TYPE_REGULAR = "delete";
    public static final String DELETE_TYPE_SAVED_AS_DRAFT = "ActionConstants ";

	// Action types
	public static final String ACTION_TYPE_CLOSE = "close";
	public static final String ACTION_TYPE_COMPLETE = "complete";
	public static final String ACTION_TYPE_COMPLETE_ACTION = "completeAction";
	public static final String ACTION_TYPE_ACTION = "action";
	public static final String START_SUB_WORKFLOW = "startSubWorkflow";
	public static final String START_CLOSE_WORKFLOW = "startCloseWorkflow";
	public static final String SYNC = "SYNC";
	public static final String MIGRATE = "MIGRATE";
	public static final String CLONE = "CLONE";
	public static final String EXPIRE = "EXPIRE";
	public static final String RETENTION = "RETENTION";
	public static final String EXPORT = "EXPORT";
	public static final String REMINDER = "REMINDER";
	public static final String ESCALATE = "ESCALATE";
}

