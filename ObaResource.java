package com.socgen.pad.obi.web.rest;

import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.framework.web.rest.interceptor.RSController;
import com.socgen.pad.obi.domain.model.MessageType;
import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.service.*;
import com.socgen.pad.obi.web.dto.*;
import com.socgen.pad.obi.web.dto.migration.MigrationRequestDto;
import com.socgen.pad.obi.web.mapper.*;
import com.socgen.pad.obi.web.rest.swagger.ObaResourceSwagger;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import static com.socgen.pad.obi.web.constants.ActionConstants.*;
import static com.socgen.pad.obi.web.constants.FeaturesConstants.*;
import static org.springframework.http.MediaType.APPLICATION_JSON_VALUE;

@RSController
@RequestMapping(path = "api/v1/obas", produces = APPLICATION_JSON_VALUE)
@AllArgsConstructor(onConstructor = @__(@Autowired))
@PreAuthorize("hasAnyAuthority('SCOPE_openid')")
@Validated
public class ObaResource extends ObaPiResource implements ObaResourceSwagger {

    private ObaService service;
    private ObaDtoMapper mapper;
    private AuditDtoMapper auditDtoMapper;
    private MessagingService<ObaPi> messagingService;
    private ExpirationObaPiService expirationObaPiService;
    private PiDtoMapper piDtoMapper;
    private ObaDtoMapper obaDtoMapper;
    private SummaryDtoMapper summaryDtoMapper;
    private MigrationProcessService migrationProcessService;
    DataRetentionService dataRetentionService;
    PiSyncService piSyncService;
    ObaSyncService obaSyncService;
    ConsumptionResponseDtoMapper dtoMapper;
    ObaPiConsumptionService obaPiConsumptionService;
    CloneConfigurationService configurationService;

    private static final String CLONE_CONFIGURATION = "clone.configuration";

	// Convenience constructor used by tests which only provide a subset of all collaborators.
	public ObaResource(
			ObaService service,
			ObaDtoMapper obaDtoMapper,
			SummaryDtoMapper summaryDtoMapper,
			AuditDtoMapper auditDtoMapper,
			MessagingService<ObaPi> messagingService,
			ExpirationObaPiService expirationObaPiService,
			PiDtoMapper piDtoMapper,
			MigrationProcessService migrationProcessService,
			DataRetentionService dataRetentionService
	) {
		this.service = service;
		this.mapper = obaDtoMapper;
		this.obaDtoMapper = obaDtoMapper;

		this.summaryDtoMapper = summaryDtoMapper;
		this.auditDtoMapper = auditDtoMapper;
		this.messagingService = messagingService;
		this.expirationObaPiService = expirationObaPiService;
		this.piDtoMapper = piDtoMapper;
		this.migrationProcessService = migrationProcessService;
		this.dataRetentionService = dataRetentionService;

		this.piSyncService = null;
		this.obaSyncService = null;
		this.dtoMapper = null;
		this.obaPiConsumptionService = null;
		this.configurationService = null;
	}

	// Convenience constructor used by tests which provide core dependencies (5 args)
	public ObaResource(
			ObaService service,
			ObaDtoMapper obaDtoMapper,
			SummaryDtoMapper summaryDtoMapper,
			AuditDtoMapper auditDtoMapper,
			MessagingService<ObaPi> messagingService
	) {
		this.service = service;
		this.mapper = obaDtoMapper;
		this.obaDtoMapper = obaDtoMapper;
		this.summaryDtoMapper = summaryDtoMapper;
		this.auditDtoMapper = auditDtoMapper;
		this.messagingService = messagingService;

		this.expirationObaPiService = null;
		this.piDtoMapper = null;
		this.migrationProcessService = null;
		this.dataRetentionService = null;
		this.piSyncService = null;
		this.obaSyncService = null;
		this.dtoMapper = null;
		this.obaPiConsumptionService = null;
		this.configurationService = null;
	}

    @Override
    @GetMapping
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "','" + OBA_MANAGER_REVIEW + "')")
    public Object queryObas(
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
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "','" + OBA_MANAGER_REVIEW + "','" + OBA_ADMIN_REVIEW + "','" + OBA_VIEW_ALL + "')")
    public Object getObaById(
            @PathVariable UUID id,
            @Parameter(description = "Scope filter: 'OWNED' for user's own OBAs, 'ALL' or null for any OBA")
            @RequestParam(required = false) com.socgen.pad.obi.web.enums.Scope scope) {
        ObaPi oba = service.getById(id);
        return mapper.toResponse(oba);
    }

    @Override
    @PostMapping
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "','" + OBA_ON_BEHALF + "')")
    public Object start(
            @RequestParam String action,
            @RequestParam(name = "activeRole") String activeRole,
            @RequestBody RequestDto request) {
        ObaPi oba = mapper.toModel(request);
        oba = service.start(oba, action, activeRole);
        messagingService.sendCreateMessageToQueue(oba);
        return mapper.toResponse(oba);
    }

    @Override
    @PutMapping("{id}/actions")
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "','" + OBA_MANAGER_REVIEW + "','" + OBA_ADMIN_REVIEW + "','" + OBA_DELETE + "','" + OBA_DELETE_SAVED_AS_DRAFT + "')")
    public Object performAction(
            @PathVariable UUID id,
            @RequestParam String action,
            @Parameter(description = "Action type to perform", schema = @Schema(allowableValues = {"complete", "close", "completeAction", "startSubWorkflow", "startCloseWorkflow", "delete", "deleteSavedAsDraft"}))
            @RequestParam String actionType,
            @RequestParam(required = false) String activeRole,
            @RequestBody RequestDto request) throws FunctionalException {
        ObaPi oba = mapper.toModel(request);
        switch (actionType) {
            case ACTION_TYPE_COMPLETE:
                oba = service.completeTask(oba, action);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            case ACTION_TYPE_CLOSE:
                oba = service.close(oba, action);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            case ACTION_TYPE_COMPLETE_ACTION:
                oba = service.completeAction(oba, action);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            case "startSubWorkflow":
                oba = service.startSubWorkflow(oba, action);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            case "startCloseWorkflow":
                oba = service.startCloseWorkflow(oba, action);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            case DELETE_TYPE_REGULAR:
                oba = service.delete(oba, action, activeRole);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            case DELETE_TYPE_SAVED_AS_DRAFT:
                oba = service.deleteSavedAsDraft(oba, action, activeRole);
                messagingService.sendUpdateMessageToQueue(oba);
                break;
            default:
                throw new IllegalArgumentException("Invalid actionType. Must be one of: complete, close, completeAction, startSubWorkflow, startCloseWorkflow, delete, deleteSavedAsDraft");
        }
        return mapper.toResponse(oba);
    }

    @Override
    @PostMapping("starts/sub-workflows/closes/{action}")
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "')")
    public Object startCloseSubWorkflow(@PathVariable String action, @RequestBody RequestAndAction requestAndAction) {
        ObaPi oba = mapper.toModel(requestAndAction.getRequest());
        oba = service.startCloseWorkflow(oba, action, requestAndAction.getActionCanBePerformed());
        messagingService.sendUpdateMessageToQueue(oba);
        return mapper.toResponse(oba);
    }

    @Override
    @PostMapping("starts/sub-workflows/{action}")
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_SUBMIT + "')")
    public Object startSubWorkflow(@PathVariable String action, @RequestBody RequestDto request) {
        ObaPi oba = mapper.toModel(request);
        oba = service.startSubWorkflow(oba, action);
        messagingService.sendUpdateMessageToQueue(oba);
        return mapper.toResponse(oba);
    }

    public Object close(String action, RequestDto request, UUID id) {
        ObaPi oba = mapper.toModel(request);
        oba = service.close(oba, action);
        messagingService.sendUpdateMessageToQueue(oba);
        return mapper.toResponse(oba);
    }

    public Object completeAction(String action, RequestDto request, UUID id) {
        ObaPi oba = mapper.toModel(request);
        oba = service.completeAction(oba, action);
        messagingService.sendUpdateMessageToQueue(oba);
        return mapper.toResponse(oba);
    }

    @Override
    @GetMapping("{id}/requesters")
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_MANAGER_REVIEW + "','" + OBA_ADMIN_REVIEW + "','" + OBA_VIEW_ALL + "')")
    public Object getByRequesterByObaId(@PathVariable UUID id) throws FunctionalException {
        return service.getByRequesterById(id);
    }

    @Override
    @PutMapping("{id}/escalations/{action}")
    @PreAuthorize("@featureSecurity.hasFeatures('" + OBA_ADMIN_REVIEW + "')")
    public Object escalate(@PathVariable String action, @PathVariable UUID id) {
        ObaPi oba = new ObaPi();
        oba.setId(id);
        oba = service.escalate(oba, action);
        messagingService.sendUpdateMessageToQueue(oba);
        return mapper.toResponse(oba);
    }

    public ResponseEntity<?> performAction(@RequestBody ObaActionRequest request) throws FunctionalException {
        String action = request.getAction() == null ? "" : request.getAction().toUpperCase();
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        switch (action) {
            case "MIGRATE":
                if (authentication == null || authentication.getAuthorities().stream().noneMatch(a -> a.getAuthority().equals(OBA_SUBMIT))) {
                    throw new AccessDeniedException("Access denied: requires OBA_SUBMIT role");
                }
                MigrationRequestDto[] migrationRequests = new MigrationRequestDto[]{request.getMigrationRequestDto()};
                List<ResponseDto> migrationResponses = new ArrayList<>();
                for (MigrationRequestDto migrationRequest : migrationRequests) {
                    ResponseDto response;
                    if (migrationRequest.getType() != null && migrationRequest.getType().toString().equals("OBA")) {
                        response = migrateOba(migrationRequest, request.getCountry());
                    } else {
                        response = migratePi(migrationRequest, request.getCountry());
                    }
                    migrationResponses.add(response);
                }
                return ResponseEntity.ok(migrationResponses);
            case "SYNC":
                if (authentication == null || authentication.getAuthorities().stream().noneMatch(a -> a.getAuthority().equals(REPORT_ADMIN))) {
                    throw new AccessDeniedException("Access denied: requires REPORT_ADMIN role");
                }
                if (request.getId() != null) {
                    obaSyncService.syncByIdAndMessageType(request.getId(), MessageType.OBA_SYNC);
                } else {
                    obaSyncService.syncAll(request.getJobId(), request.getCountry());
                }
                return ResponseEntity.ok("Sync triggered");
            case "CLONE":
                if (authentication == null || authentication.getAuthorities().stream().noneMatch(a -> a.getAuthority().equals(CLONE_CONFIGURATION))) {
                    throw new AccessDeniedException("Access denied: requires CLONE_CONFIGURATION role");
                }
                Object typeObj = request.getType();
                com.socgen.pad.obi.domain.model.ObaPiType obaPiType = com.socgen.pad.obi.domain.model.ObaPiType.valueOf(typeObj.toString());
                return ResponseEntity.ok(
                        configurationService.cloneAllFromCountry(
                                request.getCountry(),
                                request.getCountry(),
                                obaPiType
                        )
                );
            case "EXPIRE":
                expirationObaPiService.expireObaPi(request.getCountry(), request.getJobId());
                return ResponseEntity.ok("Expiration started");
            case "RETENTION":
                dataRetentionService.purgeObaPiDataByInstance(request.getJobId(), request.getInstance(), request.getType());
                return ResponseEntity.ok("Retention started");
            default:
                throw new IllegalArgumentException("Invalid action");
        }
    }

    ResponseDto migratePi(MigrationRequestDto request, String country) {
        ObaPi obaPi = piDtoMapper.toModel(request.getObaPi(), request.getType());
        obaPi = migrationProcessService.importObaPi(obaPi, request.getGgi(), request.getStatus(), request.getCreatedDate(), request.getLastModifiedDate(), country);
        return piDtoMapper.toResponse(obaPi);
    }

    ResponseDto migrateOba(MigrationRequestDto request, String country) {
        ObaPi obaPi = obaDtoMapper.toModel(request.getObaPi(), request.getType());
        obaPi = migrationProcessService.importObaPi(obaPi, request.getGgi(), request.getStatus(), request.getCreatedDate(), request.getLastModifiedDate(), country);
        return obaDtoMapper.toResponse(obaPi);
    }

    @Override
    public List<ObaSummaryDto> map(List<ObaPi> models) {
        return summaryDtoMapper.toObaSummaryDto(models);
    }

    @Override
    public List<AuditDto> auditMap(List<ObaPi> models) {
        return auditDtoMapper.toAuditDto(models);
    }

    @Override
    public List<ObaPi> getAllByEntityIds(List<String> entityIds) {
        return service.getAllByEntityIds(entityIds);
    }

    @Override
    public List<String> getAllOwnedIdsByGgi(String ggi) {
        return service.getAllOwnedIdsByGgi(ggi);
    }
}
