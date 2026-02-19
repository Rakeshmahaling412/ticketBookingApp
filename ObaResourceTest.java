package com.socgen.pad.obi.web.rest;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import java.util.*;
import java.util.UUID;
import java.util.stream.Collectors;

import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.obi.domain.model.CloneConfigurationResponse;
import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.model.ObaPiType;
import com.socgen.pad.obi.domain.model.RequesterLite;
import com.socgen.pad.obi.domain.service.*;
import com.socgen.pad.obi.web.dto.*;
import com.socgen.pad.obi.web.dto.migration.MigrationRequestDto;
import com.socgen.pad.obi.web.mapper.AuditDtoMapper;
import com.socgen.pad.obi.web.mapper.ObaDtoMapper;
import com.socgen.pad.obi.web.mapper.PiDtoMapper;
import com.socgen.pad.obi.web.mapper.SummaryDtoMapper;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.mockito.stubbing.OngoingStubbing;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;

class ObaResourceTest {

	private ObaService service;
	private ObaDtoMapper mapper;
	private SummaryDtoMapper summaryDtoMapper;
	private AuditDtoMapper auditDtoMapper;
	private MessagingService<ObaPi> messagingService;
	private ObaResource resource;

	 private ExpirationObaPiService expirationObaPiService;

	 private PiDtoMapper piDtoMapper;

	 private MigrationProcessService migrationProcessService;

	 private  DataRetentionService dataRetentionService;

	@BeforeEach
	 void setup() {
		service = mock(ObaService.class);
		mapper = mock(ObaDtoMapper.class);
		summaryDtoMapper = mock(SummaryDtoMapper.class);
		auditDtoMapper = mock(AuditDtoMapper.class);
		messagingService = mock(MessagingService.class);
		expirationObaPiService = mock(ExpirationObaPiService.class);
		piDtoMapper = mock(PiDtoMapper.class);
		migrationProcessService = mock(MigrationProcessService.class);
		dataRetentionService = mock(DataRetentionService.class);

		resource = new ObaResource(
				service, mapper, summaryDtoMapper, auditDtoMapper, messagingService,
				expirationObaPiService, piDtoMapper, migrationProcessService, dataRetentionService
		);
		resource.obaSyncService = mock(ObaSyncService.class);
		resource.configurationService = mock(CloneConfigurationService.class);
		// Clear SecurityContext before each test
		SecurityContextHolder.clearContext();
	}

	@Test
	 void testQueryObasWithSelfTodoFilter() {
		List<String> roles = Arrays.asList("role1", "role2");
		List<ObaPi> obaPis = Collections.singletonList(new ObaPi());
		List<AuditDto> auditDtos = Collections.singletonList(new AuditDto());

		when(service.getAllAssignedToSelfByRoles(roles)).thenReturn(obaPis);
		when(auditDtoMapper.toAuditDto(obaPis)).thenReturn(auditDtos);

		Object result = resource.queryObas(roles, "self-todo");

		verify(service).getAllAssignedToSelfByRoles(roles);
		verify(auditDtoMapper).toAuditDto(obaPis);
		assertEquals(auditDtos, result);
	}

	@Test
	 void testQueryObasWithHistoryFilter() {
		List<String> roles = Arrays.asList("role1");
		List<ObaPi> obaPis = Collections.singletonList(new ObaPi());
		List<AuditDto> auditDtos = Collections.singletonList(new AuditDto());

		when(service.getAllHistoryByRoles(roles)).thenReturn(obaPis);
		when(auditDtoMapper.toAuditDto(obaPis)).thenReturn(auditDtos);

		Object result = resource.queryObas(roles, "history");

		verify(service).getAllHistoryByRoles(roles);
		verify(auditDtoMapper).toAuditDto(obaPis);
		assertEquals(auditDtos, result);
	}

	@Test
	 void testQueryObasThrowsExceptionOnInvalidFilter() {
		List<String> roles = Arrays.asList("role1");

		IllegalArgumentException ex = assertThrows(IllegalArgumentException.class, () -> {
			resource.queryObas(roles, "invalid-filter");
		});

		assertEquals("Invalid filter or missing roles parameter", ex.getMessage());
	}

	@Test
	 void testQueryObasThrowsExceptionWhenParamsNull() {
		IllegalArgumentException ex1 = assertThrows(IllegalArgumentException.class,
				() -> resource.queryObas(null, "self-todo")
		);
		List<String> rolesParam = Arrays.asList("role1");
		IllegalArgumentException ex2 = assertThrows(IllegalArgumentException.class,
				() -> resource.queryObas(rolesParam, null)
		);

		assertEquals("Invalid filter or missing roles parameter", ex1.getMessage());
		assertEquals("Invalid filter or missing roles parameter", ex2.getMessage());
	}

	@Test
	 void testGetObaById() {
		UUID id = UUID.randomUUID();
		ObaPi obaPi = new ObaPi();
		ResponseDto responseDto = new ResponseDto();

		when(service.getById(id)).thenReturn(obaPi);
		when(mapper.toResponse(obaPi)).thenReturn(responseDto);

		Object result = resource.getObaById(id, null);

		verify(service).getById(id);
		verify(mapper).toResponse(obaPi);
		assertEquals(responseDto, result);
	}

	@Test
	 void testStart() {
		String action = "someAction";
		String activeRole = "someRole";
		RequestDto requestDto = new RequestDto();
		ObaPi obaPiModel = new ObaPi();
		ObaPi obaPiStarted = new ObaPi();
		ResponseDto responseDto = new ResponseDto();

		when(mapper.toModel(requestDto)).thenReturn(obaPiModel);
		when(service.start(obaPiModel, action, activeRole)).thenReturn(obaPiStarted);
		when(mapper.toResponse(obaPiStarted)).thenReturn(responseDto);

		Object result = resource.start(action, activeRole, requestDto);

		verify(service).start(obaPiModel, action, activeRole);
		verify(messagingService).sendCreateMessageToQueue(obaPiStarted);
		verify(mapper).toResponse(obaPiStarted);
		assertEquals(responseDto, result);
	}

	@Test
	 void testPerformActionComplete() throws Exception {
		performActionTestHelper("complete", (s, oba, action) -> s.completeTask(oba, action));
	}

	@Test
	 void testPerformActionClose() throws Exception {
		performActionTestHelper("close", (s, oba, action) -> s.close(oba, action));
	}

	@Test
	 void testPerformActionCompleteAction() throws Exception {
		performActionTestHelper("completeAction", (s, oba, action) -> s.completeAction(oba, action));
	}

	@Test
	 void testPerformActionStartSubWorkflow() throws Exception {
		performActionTestHelper("startSubWorkflow", (s, oba, action) -> s.startSubWorkflow(oba, action));
	}

	@Test
	 void testPerformActionStartCloseWorkflow() throws Exception {
		performActionTestHelper("startCloseWorkflow", (s, oba, action) -> s.startCloseWorkflow(oba, action));
	}

	@Test
	 void testPerformActionDelete() throws Exception {
		performActionDeleteHelper("regular", ObaPiService::delete);
	}

	@Test
	 void testPerformActionDeleteSavedAsDraft() throws Exception {
		performActionDeleteHelper("savedAsDraft", ObaPiService::deleteSavedAsDraft);
	}

	@Test
	 void testPerformActionThrowsExceptionOnInvalidActionType() {
		RequestDto requestDto = new RequestDto();
		ObaPi obaPiModel = new ObaPi();

		when(mapper.toModel(requestDto)).thenReturn(obaPiModel);

		UUID id = UUID.randomUUID();
		IllegalArgumentException ex = assertThrows(IllegalArgumentException.class, () ->
				resource.performAction(id, "action", "invalidActionType", null, requestDto)
		);

		assertTrue(ex.getMessage().contains("Invalid actionType"));
	}

	@Test
	 void testMap() {
		List<ObaPi> models = Collections.singletonList(new ObaPi());
		List<ObaSummaryDto> dtos = Collections.singletonList(new ObaSummaryDto());

		when(summaryDtoMapper.toObaSummaryDto(models)).thenReturn(dtos);

		List<ObaSummaryDto> result = resource.map(models);

		verify(summaryDtoMapper).toObaSummaryDto(models);
		assertEquals(dtos, result);
	}

	@Test
	 void testAuditMap() {
		List<ObaPi> models = Collections.singletonList(new ObaPi());
		List<AuditDto> dtos = Collections.singletonList(new AuditDto());

		when(auditDtoMapper.toAuditDto(models)).thenReturn(dtos);

		List<AuditDto> result = resource.auditMap(models);

		verify(auditDtoMapper).toAuditDto(models);
		assertEquals(dtos, result);
	}

	@Test
	 void testGetAllByEntityIds() {
		List<String> entityIds = Arrays.asList("id1", "id2");
		List<ObaPi> obaPis = Collections.singletonList(new ObaPi());

		when(service.getAllByEntityIds(entityIds)).thenReturn(obaPis);

		List<ObaPi> result = resource.getAllByEntityIds(entityIds);

		verify(service).getAllByEntityIds(entityIds);
		assertEquals(obaPis, result);
	}

	@Test
	void testGetAllOwnedIdsByGgi() {
		String ggi = "someGgi";
		List<String> ids = Arrays.asList("id1", "id2");

		when(service.getAllOwnedIdsByGgi(ggi)).thenReturn(ids);

		List<String> result = resource.getAllOwnedIdsByGgi(ggi);

		verify(service).getAllOwnedIdsByGgi(ggi);
		assertEquals(ids, result);
	}

	@Test
	 void testGetByRequesterByObaId() throws Exception {
		UUID id = UUID.randomUUID();
		RequesterLite requesterLite = new RequesterLite();

		when(service.getByRequesterById(id)).thenReturn(requesterLite);

		Object result = resource.getByRequesterByObaId(id);

		verify(service).getByRequesterById(id);
		assertEquals(requesterLite, result);
	}

	// Helper interfaces and methods for performAction tests

	@FunctionalInterface
	interface ServiceAction {
		ObaPi apply(ObaService service, ObaPi oba, String action) throws Exception;
	}

	@FunctionalInterface
	interface ServiceDeleteAction {
		ObaPi apply(ObaService service, ObaPi oba, String action, String activeRole) throws Exception;
	}

	 void performActionTestHelper(String actionType, ServiceAction serviceCall) throws Exception {
		UUID id = UUID.randomUUID();
		String action = "action";
		RequestDto requestDto = new RequestDto();
		ObaPi obaPiModel = new ObaPi();
		ObaPi obaPiResult = new ObaPi();
		ResponseDto responseDto = new ResponseDto();

		when(mapper.toModel(requestDto)).thenReturn(obaPiModel);
		when(serviceCall.apply(service, obaPiModel, action)).thenReturn(obaPiResult);
		when(mapper.toResponse(obaPiResult)).thenReturn(responseDto);

		Object result = resource.performAction(id, action, actionType, null, requestDto);

		verify(messagingService).sendUpdateMessageToQueue(obaPiResult);
		verify(mapper).toResponse(obaPiResult);
		assertEquals(responseDto, result);
	}

	 void performActionDeleteHelper(String actionType, ServiceDeleteAction serviceCall) throws Exception {
		UUID id = UUID.randomUUID();
		String action = "action";
		String activeRole = "role";
		RequestDto requestDto = new RequestDto();
		ObaPi obaPiModel = new ObaPi();
		ObaPi obaPiResult = new ObaPi();
		ResponseDto responseDto = new ResponseDto();

		when(mapper.toModel(requestDto)).thenReturn(obaPiModel);
		when(serviceCall.apply(service, obaPiModel, action, activeRole)).thenReturn(obaPiResult);
		when(mapper.toResponse(obaPiResult)).thenReturn(responseDto);

		Object result = resource.performAction(id, action, actionType, activeRole, requestDto);

		verify(messagingService).sendUpdateMessageToQueue(obaPiResult);
		verify(mapper).toResponse(obaPiResult);
		assertEquals(responseDto, result);
	}


}

