package com.socgen.pad.obi.web.rest;


import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.framework.domain.service.impl.SgConnectHelper;
import com.socgen.pad.framework.web.rest.interceptor.RSController;
import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.model.Property;
import com.socgen.pad.obi.domain.service.ObaService;
import com.socgen.pad.obi.domain.service.PropertyService;
import com.socgen.pad.obi.domain.service.ValidatorService;
import com.socgen.pad.obi.web.mapper.PropertyDtoMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RSController
@PreAuthorize("hasAnyAuthority('SCOPE_openid')")
public abstract class ObaPiResource {

	@Autowired
	private PropertyService propertyService;
	@Autowired
	private PropertyDtoMapper propertyMapper;
	@Autowired
	private SgConnectHelper sgConnectHelper;
	@Autowired
	private ValidatorService validatorService;
	@Autowired
	private ObaService obaService;

	abstract Object map(List<ObaPi> models);

	abstract Object auditMap(List<ObaPi> models);

	abstract List<ObaPi> getAllByEntityIds(List<String> entityIds);

	abstract List<String> getAllOwnedIdsByGgi(String ggi);



	@GetMapping("{id}/properties")
	@Operation(summary = "Get properties by id with optional key filter", description = "Get all properties or a specific property by id. Use 'key' parameter to get a single property value")
			@ApiResponse(responseCode = "200", description = "Successful Operation", content = @Content(mediaType = "application/json"))
			@ApiResponse(responseCode = "400", description = "Invalid request", content = @Content(mediaType = "application/json"))
			@ApiResponse(responseCode = "500", description = "Internal server error", content = @Content(mediaType = "application/json"))
	public Object getPropertiesByEntityId(
			@PathVariable(value = "id") String id,
			@RequestParam(value = "key", required = false) String key) throws FunctionalException {
		if (key != null) {
			return propertyService.getValueByEntityIdAndKey(id, key);
		}
		List<Property> properties = propertyService.getAllByEntityId(id);
		return propertyMapper.toDtos(properties);
	}

	@PostMapping("{id}/properties")
	@Operation(summary = "Update properties by id", description = "Update properties by id")
			@ApiResponse(responseCode = "200", description = "Successful Operation", content = @Content(mediaType = "application/json"))
			@ApiResponse(responseCode = "400", description = "Invalid request", content = @Content(mediaType = "application/json"))
			@ApiResponse(responseCode = "500", description = "Internal server error", content = @Content(mediaType = "application/json"))
	public void createOrUpdate(@PathVariable(value = "id") String id, @RequestBody Map<String, String> propertyMap) {
		propertyService.createOrUpdate(id, propertyMap);
	}

	@GetMapping("validators")
	@Operation(summary = "Get validators by type and action", description = "Get validators by type and action using query parameters")
			@ApiResponse(responseCode = "200", description = "Successful Operation", content = @Content(mediaType = "application/json"))
			@ApiResponse(responseCode = "400", description = "Invalid request", content = @Content(mediaType = "application/json"))
			@ApiResponse(responseCode = "500", description = "Internal server error", content = @Content(mediaType = "application/json"))
	public Object getValidators(
			@RequestParam(value = "type") String type,
			@RequestParam(value = "action") String action) {
		return validatorService.getValidators(type, action, sgConnectHelper.getConnectedUser().getCountry());
	}

}
