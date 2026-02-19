package com.socgen.pad.obi.web.rest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.*;

import java.util.Arrays;
import java.util.List;
import java.util.UUID;

import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.model.RequesterLite;
import com.socgen.pad.obi.domain.service.MessagingService;
import com.socgen.pad.obi.domain.service.PiService;
import com.socgen.pad.obi.domain.service.PiSyncService;
import com.socgen.pad.obi.web.dto.AuditDto;
import com.socgen.pad.obi.web.dto.RequestDto;
import com.socgen.pad.obi.web.dto.ResponseDto;
import com.socgen.pad.obi.web.enums.Scope;
import com.socgen.pad.obi.web.mapper.AuditDtoMapper;
import com.socgen.pad.obi.web.mapper.PiDtoMapper;
import com.socgen.pad.obi.web.mapper.SummaryDtoMapper;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
public class PiResourceTest {

	@Mock
	private PiService service;
	@Mock
	private PiDtoMapper mapper;
	@Mock
	private SummaryDtoMapper summaryDtoMapper;
	@Mock
	private AuditDtoMapper auditDtoMapper;
	@Mock
	private MessagingService<ObaPi> messagingService;
	@Mock
	private  PiSyncService piSyncService;

	private PiResource controller;

	@Before
	public void setup() {
		MockitoAnnotations.openMocks(this);
		controller = new PiResource(service, mapper, summaryDtoMapper, auditDtoMapper, messagingService,piSyncService);
	}

	@Test
	public void queryPis_shouldReturnAuditDtos_whenFilterSelfTodo() {
		List<String> roles = Arrays.asList("role1", "role2");
		List<ObaPi> todoList = Arrays.asList(new ObaPi(), new ObaPi());
		List<AuditDto> auditDtos = Arrays.asList(new AuditDto(), new AuditDto());

		when(service.getAllAssignedToSelfByRoles(roles)).thenReturn(todoList);
		when(auditDtoMapper.toAuditDto(todoList)).thenReturn(auditDtos);

		Object result = controller.queryPis(roles, "self-todo");

		assertThat(result).isEqualTo(auditDtos);
		verify(service).getAllAssignedToSelfByRoles(roles);
		verify(auditDtoMapper).toAuditDto(todoList);
	}

	@Test
	public void queryPis_shouldReturnAuditDtos_whenFilterHistory() {
		List<String> roles = Arrays.asList("role1");
		List<ObaPi> historyList = Arrays.asList(new ObaPi());
		List<AuditDto> auditDtos = Arrays.asList(new AuditDto());

		when(service.getAllHistoryByRoles(roles)).thenReturn(historyList);
		when(auditDtoMapper.toAuditDto(historyList)).thenReturn(auditDtos);

		Object result = controller.queryPis(roles, "history");

		assertThat(result).isEqualTo(auditDtos);
		verify(service).getAllHistoryByRoles(roles);
		verify(auditDtoMapper).toAuditDto(historyList);
	}

	@Test
	public void queryPis_shouldThrowIllegalArgumentException_whenFilterIsNull() {
		List<String> roles = Arrays.asList("role1");
		assertThatThrownBy(() -> controller.queryPis(roles, null))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("Invalid filter or missing roles parameter");
	}

	@Test
	public void queryPis_shouldThrowIllegalArgumentException_whenRolesIsNull() {
		assertThatThrownBy(() -> controller.queryPis(null, "self-todo"))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("Invalid filter or missing roles parameter");
	}

	@Test
	public void queryPis_shouldThrowIllegalArgumentException_whenFilterIsInvalid() {
		List<String> roles = Arrays.asList("role1");
		assertThatThrownBy(() -> controller.queryPis(roles, "invalid-filter"))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("Invalid filter or missing roles parameter");
	}

	@Test
	public void getPiById_shouldReturnMappedResponse() {
		UUID id = UUID.randomUUID();
		ObaPi pi = new ObaPi();
		ResponseDto mappedResponse = new ResponseDto();

		when(service.getById(id)).thenReturn(pi);
		when(mapper.toResponse(pi)).thenReturn(mappedResponse);

		Object response = controller.getPiById(id, Scope.ALL);

		assertThat(response).isEqualTo(mappedResponse);
		verify(service).getById(id);
		verify(mapper).toResponse(pi);
	}

	@Test
	public void start_shouldStartPiAndSendMessage() {
		String action = "startAction";
		String activeRole = "roleX";
		RequestDto request = new RequestDto();
		ObaPi piModel = new ObaPi();
		ObaPi startedPi = new ObaPi();
		ResponseDto responseDto = new ResponseDto();

		when(mapper.toModel(request)).thenReturn(piModel);
		when(service.start(piModel, action, activeRole)).thenReturn(startedPi);
		when(mapper.toResponse(startedPi)).thenReturn(responseDto);

		Object response = controller.start(action, activeRole, request);

		assertThat(response).isEqualTo(responseDto);
		verify(service).start(piModel, action, activeRole);
		verify(messagingService).sendCreateMessageToQueue(startedPi);
	}

	@Test
	public void performAction_shouldCompleteTaskAndSendMessage_whenActionTypeComplete() throws Exception {
		performActionTestTemplate("complete", (service, pi, action) -> service.completeTask(pi, action));
	}

	@Test
	public void performAction_shouldCloseAndSendMessage_whenActionTypeClose() throws Exception {
		performActionTestTemplate("close", (service, pi, action) -> service.close(pi, action));
	}

	@Test
	public void performAction_shouldCompleteActionAndSendMessage_whenActionTypeCompleteAction() throws Exception {
		performActionTestTemplate("action", (service, pi, action) -> service.completeAction(pi, action));
	}

	@Test
	public void performAction_shouldStartSubWorkflowAndSendMessage_whenActionTypeStartSubWorkflow() throws Exception {
		performActionTestTemplate("startSubWorkflow", (service, pi, action) -> service.startSubWorkflow(pi, action));
	}

	@Test
	public void performAction_shouldStartCloseWorkflowAndSendMessage_whenActionTypeStartCloseWorkflow() throws Exception {
		performActionTestTemplate("startCloseWorkflow", (service, pi, action) -> service.startCloseWorkflow(pi, action));
	}

	@Test
	public void performAction_shouldDeleteAndSendMessage_whenActionTypeDelete() throws Exception {
		performActionTestTemplate("regular", (service, pi, action) -> service.delete(pi, action, "activeRole"));
	}

	@Test
	public void performAction_shouldDeleteSavedAsDraftAndSendMessage_whenActionTypeDeleteSavedAsDraft() throws Exception {
		performActionTestTemplate("savedAsDraft", (service, pi, action) -> service.deleteSavedAsDraft(pi, action, "activeRole"));
	}

	@Test
	public void performAction_shouldThrowIllegalArgumentException_whenInvalidActionType() {
		UUID id = UUID.randomUUID();
		RequestDto request = new RequestDto();

		assertThatThrownBy(() -> controller.performAction(id, "someAction", "invalidType", null, request))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("Invalid actionType");
	}

	@FunctionalInterface
	private interface ActionCall {
		ObaPi call(PiService service, ObaPi pi, String action) throws Exception;
	}

	private void performActionTestTemplate(String actionType, ActionCall actionCall) throws Exception {
		UUID id = UUID.randomUUID();
		String action = "someAction";
		String activeRole = "activeRole";
		RequestDto request = new RequestDto();
		ObaPi piModel = new ObaPi();
		ObaPi returnedPi = new ObaPi();
		ResponseDto responseDto = new ResponseDto();

		when(mapper.toModel(request)).thenReturn(piModel);
		// Use spy for service to mock specific method dynamically
		PiService spyService = spy(service);

		// Mock the specific service method call to return returnedPi
		switch (actionType) {
			case "complete":
				doReturn(returnedPi).when(spyService).completeTask(piModel, action);
				break;
			case "close":
				doReturn(returnedPi).when(spyService).close(piModel, action);
				break;
			case "action":
				doReturn(returnedPi).when(spyService).completeAction(piModel, action);
				break;
			case "startSubWorkflow":
				doReturn(returnedPi).when(spyService).startSubWorkflow(piModel, action);
				break;
			case "startCloseWorkflow":
				doReturn(returnedPi).when(spyService).startCloseWorkflow(piModel, action);
				break;
			case "regular":
				doReturn(returnedPi).when(spyService).delete(piModel, action, activeRole);
				break;
			case "savedAsDraft":
				doReturn(returnedPi).when(spyService).deleteSavedAsDraft(piModel, action, activeRole);
				break;
			default:
				throw new IllegalArgumentException("Unsupported actionType for test");
		}

		// Replace controller's service with spy
		controller = new PiResource(spyService, mapper, summaryDtoMapper, auditDtoMapper, messagingService,piSyncService);

		when(mapper.toResponse(returnedPi)).thenReturn(responseDto);

		Object response;
		if ("regular".equals(actionType) || "savedAsDraft".equals(actionType)) {
			response = controller.performAction(id, action, actionType, activeRole, request);
		} else {
			response = controller.performAction(id, action, actionType, null, request);
		}

		assertThat(response).isEqualTo(responseDto);

		// Verify correct service method called
		switch (actionType) {
			case "complete":
				verify(spyService).completeTask(piModel, action);
				break;
			case "close":
				verify(spyService).close(piModel, action);
				break;
			case "action":
				verify(spyService).completeAction(piModel, action);
				break;
			case "startSubWorkflow":
				verify(spyService).startSubWorkflow(piModel, action);
				break;
			case "startCloseWorkflow":
				verify(spyService).startCloseWorkflow(piModel, action);
				break;
			case "regular":
				verify(spyService).delete(piModel, action, activeRole);
				break;
			case "savedAsDraft":
				verify(spyService).deleteSavedAsDraft(piModel, action, activeRole);
				break;
		}

		// Verify message sent
		verify(messagingService).sendUpdateMessageToQueue(returnedPi);
	}

	@Test
	public void getByRequesterByPiId_shouldReturnRequesterLite() throws Exception {
		UUID id = UUID.randomUUID();
		RequesterLite requester = new RequesterLite();

		when(service.getByRequesterById(id)).thenReturn(requester);

		Object response = controller.getByRequesterByPiId(id);

		assertThat(response).isEqualTo(requester);
		verify(service).getByRequesterById(id);
	}
}