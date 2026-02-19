package com.socgen.pad.obi.web.rest;

import static org.apache.commons.lang3.RandomStringUtils.randomAlphabetic;
import static org.assertj.core.api.Assertions.assertThat;
import static org.joda.time.DateTime.now;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

import java.util.UUID;

import org.jeasy.random.EasyRandom;
import org.jeasy.random.EasyRandomParameters;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.obi.domain.model.ObaPiType;
import com.socgen.pad.obi.domain.service.RepairWorkflowAndEntityPropertiesService;
import com.socgen.pad.obi.domain.utils.PerformedActionNameEnum;
import com.socgen.pad.obi.web.dto.ResponseDto;

@RunWith(MockitoJUnitRunner.class)
public class RepairWorkflowAndEntityPropertiesResourceTest {

	@Mock
	private RepairWorkflowAndEntityPropertiesService service;
	private RepairWorkflowAndEntityPropertiesResource controller;
	private EasyRandom random;

	@Before
	public void setup() {
		initMocks(this);
		controller = new RepairWorkflowAndEntityPropertiesResource(service);
		random = new EasyRandom(new EasyRandomParameters()
				.seed(now().getMillis())
				.randomize(String.class, () -> randomAlphabetic(12)));
	}

	@Test
	public void shouldRepairEngineTask() throws FunctionalException {
		// Given
		UUID id = UUID.randomUUID();
		ObaPiType type = ObaPiType.OBA;
		String completedBy = random.nextObject(String.class);
		boolean isBatchTask = false;
		 PerformedActionNameEnum performedActionName = PerformedActionNameEnum.ADMIN_APPROVED;
		ResponseDto expected = random.nextObject(ResponseDto.class);
		when(service.repairEngineTaskAndObaPiProperties(id, performedActionName.name(), completedBy, isBatchTask, type)).thenReturn(expected);
		// When
		Object response = controller.repairEngineTaskAndObaPiProperties(type, id, performedActionName, completedBy, isBatchTask);
		// Then
		assertThat(response).isEqualTo(expected);
	}
}
