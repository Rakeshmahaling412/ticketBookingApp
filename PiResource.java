package com.socgen.pad.obi.web.rest;

import static com.socgen.pad.obi.web.constants.ActionConstants.*;
import static com.socgen.pad.obi.web.constants.FeaturesConstants.*;
import static org.springframework.http.MediaType.APPLICATION_JSON_VALUE;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import com.socgen.pad.obi.domain.model.MessageType;
import com.socgen.pad.obi.domain.service.PiSyncService;
import com.socgen.pad.obi.web.enums.Scope;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.framework.web.rest.interceptor.RSController;
import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.service.MessagingService;
import com.socgen.pad.obi.domain.service.PiService;
import com.socgen.pad.obi.web.dto.AuditDto;
import com.socgen.pad.obi.web.dto.PiSummaryDto;
import com.socgen.pad.obi.web.dto.RequestDto;
import com.socgen.pad.obi.web.mapper.AuditDtoMapper;
import com.socgen.pad.obi.web.mapper.PiDtoMapper;
import com.socgen.pad.obi.web.mapper.SummaryDtoMapper;
import com.socgen.pad.obi.web.rest.swagger.PiResourceSwagger;

import lombok.AllArgsConstructor;

@RSController
@RequestMapping(path = "api/v1/private-investments", produces = APPLICATION_JSON_VALUE)
@AllArgsConstructor
@Validated
@PreAuthorize("hasAnyAuthority('SCOPE_openid')")
public class PiResource extends ObaPiResource implements PiResourceSwagger {

	private PiService service;
	private PiDtoMapper mapper;
	private SummaryDtoMapper summaryDtoMapper;
	private AuditDtoMapper auditDtoMapper;
	private MessagingService<ObaPi> messagingService;
	private final PiSyncService piSyncService;


	@Override
	@GetMapping
	@PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "','" + PI_MANAGER_REVIEW + "')")
	public Object queryPis(
			@RequestParam(required = false) List<String> roles,
			@Parameter(description = "Filter type", schema = @Schema(allowableValues = {"self-todo", "history"}))
			@RequestParam(required = false) String filter) {
		if (filter == null || roles == null) {
			throw new IllegalArgumentException("Invalid filter or missing roles parameter");
		}

		switch (filter) {
			case FILTER_SELF_TODO:
				List<ObaPi> todoResults = service.getAllAssignedToSelfByRoles(roles);
				return auditDtoMapper.toAuditDto(todoResults);
			case FILTER_HISTORY:
				List<ObaPi> historyResults = service.getAllHistoryByRoles(roles);
				return auditDtoMapper.toAuditDto(historyResults);
			default:
				throw new IllegalArgumentException("Invalid filter or missing roles parameter");
		}
	}

	@Override
	@GetMapping("{id}")
	@PreAuthorize("@featureSecurity.hasFeatures('" + PI_SUBMIT + "','" + PI_MANAGER_REVIEW + "','" + PI_ADMIN_REVIEW+ "','" + PI_VIEW_ALL + "')")
	public Object getPiById(
			@PathVariable UUID id,
			@Parameter(description = "Scope filter: 'OWNED' for user's own PIs, 'ALL' or null for any PI")
			@RequestParam(required = false) Scope scope) {
		ObaPi pi;
        pi = service.getById(id);
        return mapper.toResponse(pi);
	}

	@Override
	@PostMapping
	@PreAuthorize("@featureSecurity.hasFeatures('" + PI_SUBMIT + "', '" + PI_ON_BEHALF + "')")
	public Object start(
			@RequestParam String action,
			@RequestParam(name = "activeRole") String activeRole,
			@RequestBody RequestDto request) {
		ObaPi pi = mapper.toModel(request);
		pi = service.start(pi, action, activeRole);
		messagingService.sendCreateMessageToQueue(pi);
		return mapper.toResponse(pi);
	}

	@Override
	@PutMapping("{id}/actions")
	@PreAuthorize("@featureSecurity.hasFeatures('" + PI_SUBMIT + "','" + PI_MANAGER_REVIEW + "','" + PI_ADMIN_REVIEW + "','" + PI_DELETE + "','" + PI_DELETE_SAVED_AS_DRAFT + "')")
	public Object performAction(
			@PathVariable @Parameter(description = "Unique identifier of the Private Investment") UUID id,
			@RequestParam @Parameter(description = "Action name to perform") String action,
			@RequestParam @Parameter(
					description = "Action type to perform",
					schema = @Schema(allowableValues = {"complete", "close", "completeAction", "startSubWorkflow", "startCloseWorkflow", "delete", "deleteSavedAsDraft"})
			) String actionType,
			@RequestParam(required = false) @Parameter(description = "Active role of the user (required for delete actions)") String activeRole,
			@RequestBody RequestDto request) throws FunctionalException {
		ObaPi pi = mapper.toModel(request);

		switch (actionType) {
			case ACTION_TYPE_COMPLETE:
				pi = service.completeTask(pi, action);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			case ACTION_TYPE_CLOSE:
				pi = service.close(pi, action);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			case ACTION_TYPE_ACTION:
				pi = service.completeAction(pi, action);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			case "startSubWorkflow":
				pi = service.startSubWorkflow(pi, action);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			case "startCloseWorkflow":
				pi = service.startCloseWorkflow(pi, action);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			case DELETE_TYPE_REGULAR:
				pi = service.delete(pi, action, activeRole);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			case DELETE_TYPE_SAVED_AS_DRAFT:
				pi = service.deleteSavedAsDraft(pi, action, activeRole);
				messagingService.sendUpdateMessageToQueue(pi);
				break;
			default:
				throw new IllegalArgumentException("Invalid actionType. Must be one of: complete, close, completeAction, startSubWorkflow, startCloseWorkflow, delete, deleteSavedAsDraft");
		}

		return mapper.toResponse(pi);
	}

	@Override
	public List<String> getAllOwnedIdsByGgi(String ggi) {
		return service.getAllOwnedIdsByGgi(ggi);
	}

	@Override
	public List<ObaPi> getAllByEntityIds(List<String> entityIds) {
		return service.getAllByEntityIds(entityIds);
	}

	@Override
	public List<PiSummaryDto> map(List<ObaPi> models) {
		return summaryDtoMapper.toPiSummaryDto(models);
	}

	@Override
	public List<AuditDto> auditMap(List<ObaPi> models) {
		return auditDtoMapper.toAuditDto(models);
	}

	@GetMapping("{id}/requesters")
	@PreAuthorize("@featureSecurity.hasFeatures('" + PI_MANAGER_REVIEW + "','" + PI_ADMIN_REVIEW+ "','" + PI_VIEW_ALL + "')")
	public Object getByRequesterByPiId(@PathVariable UUID id) throws FunctionalException {
		return service.getByRequesterById(id);
	}

	@Override
	@PostMapping("/syncs")
	@PreAuthorize("@featureSecurity.hasFeatures('" + REPORT_ADMIN + "') OR hasAnyAuthority('SCOPE_api.personal-account-dealing-oba-pi.v1')")
	public Object sync(
			@RequestParam(name = "country", required = false) String country,
			@RequestParam(name = "id", required = false) UUID id,
			@RequestParam(name = "jobId", required = false) UUID jobId) {

		if (id != null) {
			piSyncService.syncByIdAndMessageType(id, MessageType.PI_SYNC);
			return "synced";
		} else if (country != null) {
			piSyncService.syncAll(jobId, country);
			return "PI synchronization for " + country + " started at " + LocalDateTime.now();
		} else {
			throw new IllegalArgumentException("Either 'country' or 'id' parameter must be provided");
		}
	}


}
