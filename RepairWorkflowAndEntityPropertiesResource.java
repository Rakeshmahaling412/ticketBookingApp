package com.socgen.pad.obi.web.rest;

import static org.springframework.http.MediaType.APPLICATION_JSON_VALUE;
import static com.socgen.pad.obi.web.constants.FeaturesConstants.REPAIR_WORKFLOW;

import java.util.UUID;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.framework.web.rest.interceptor.RSController;
import com.socgen.pad.obi.domain.model.ObaPiType;
import com.socgen.pad.obi.domain.service.RepairWorkflowAndEntityPropertiesService;
import com.socgen.pad.obi.domain.utils.PerformedActionNameEnum;
import com.socgen.pad.obi.web.rest.swagger.RepairWorkflowAndEntityPropertiesResourceSwagger;

import lombok.AllArgsConstructor;

@RSController
@RequestMapping(path = "api/v1/repairs", produces = APPLICATION_JSON_VALUE)
@AllArgsConstructor
@PreAuthorize("hasAnyAuthority('SCOPE_openid')")
public class RepairWorkflowAndEntityPropertiesResource implements RepairWorkflowAndEntityPropertiesResourceSwagger {

    private final RepairWorkflowAndEntityPropertiesService service;

    @Override
    @PutMapping("{id}")
    @PreAuthorize("@featureSecurity.hasFeatures('" + REPAIR_WORKFLOW + "')")
    public Object repairEngineTaskAndObaPiProperties(
	    @RequestParam(value = "type", required = true) ObaPiType type,
	    @PathVariable("id") UUID id,
	    @RequestParam(value = "performedActionName", required = true) PerformedActionNameEnum performedActionName,
	    @RequestParam(value = "completedBy", required = true) String completedBy,
	    @RequestParam(value = "isBatchTask", required = false) boolean isBatchTask) throws FunctionalException {
    	return service.repairEngineTaskAndObaPiProperties(id, performedActionName.name(), completedBy, isBatchTask,type);
    }

}
