package com.socgen.pad.obi.web.rest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import com.socgen.pad.obi.domain.service.*;
import com.socgen.pad.obi.util.Helper;
import com.socgen.pad.obi.web.mapper.*;
import org.jeasy.random.EasyRandom;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.util.ReflectionTestUtils;
import com.socgen.pad.framework.domain.model.PadUser;
import com.socgen.pad.framework.domain.service.impl.SgConnectHelper;
import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.model.Property;
import com.socgen.pad.obi.domain.model.Validator;

@RunWith(SpringRunner.class)
public class ObaPiResourceTest {

	@Mock
	private PropertyService propertyService;
	@Mock
	private PropertyDtoMapper propertyMapper;
	@Mock
	private SgConnectHelper sgConnectHelper;
	@Mock
	private ValidatorService validatorService;
	@Mock
	private ObaService obaService;
	@Mock
	private ObaDtoMapper obaDtoMapper;
	@Mock
	private SummaryDtoMapper summaryDtoMapper;
	@Mock
	private AuditDtoMapper auditDtoMapper;
	@Mock
	private MessagingService<ObaPi> messagingService;



	@Mock
	private ExpirationObaPiService expirationObaPiService;

	@Mock
	private PiDtoMapper piDtoMapper;


	@Mock
	private MigrationProcessService migrationProcessService;

	@Mock
	private  DataRetentionService dataRetentionService;

	private ObaResource controller;

	private EasyRandom random;

	@Before
	public void setup() {
		random = new EasyRandom();
		// Manually instantiate controller with constructor dependencies
		controller = new ObaResource(obaService, obaDtoMapper, summaryDtoMapper, auditDtoMapper, messagingService,expirationObaPiService,piDtoMapper,migrationProcessService,dataRetentionService);
		// Manually inject mocked dependencies into parent class fields
		ReflectionTestUtils.setField(controller, "propertyService", propertyService);
		ReflectionTestUtils.setField(controller, "propertyMapper", propertyMapper);
		ReflectionTestUtils.setField(controller, "sgConnectHelper", sgConnectHelper);
		ReflectionTestUtils.setField(controller, "validatorService", validatorService);
	}

	@Test
	public void shouldReturnValidators() {
		// GIven
		String type = random.nextObject(String.class);
		String action = random.nextObject(String.class);
		EasyRandom easyRandom = Helper.getEasyRandomForSgConnectClaimAccessor();
		PadUser connectedUser = easyRandom.nextObject(PadUser.class);
		when(sgConnectHelper.getConnectedUser()).thenReturn(connectedUser);
		List<Validator> expected = random.objects(Validator.class, 5).collect(Collectors.toList());
		when(validatorService.getValidators(type, action, connectedUser.getCountry())).thenReturn(expected);
		// When
		Object response = controller.getValidators(type, action);
		// Then
		assertThat(response).isEqualTo(expected);
	}

	@Test
	public void shouldReturnPropertiesByEntityIdWithKey() throws Exception {
		String id = random.nextObject(String.class);
		String key = random.nextObject(String.class);
		String expected = "propertyValue";
		when(propertyService.getValueByEntityIdAndKey(id, key)).thenReturn(expected);
		Object response = controller.getPropertiesByEntityId(id, key);
		assertThat(response).isEqualTo(expected);
	}

	@Test
	public void shouldReturnPropertiesByEntityIdWithoutKey() throws Exception {
		String id = random.nextObject(String.class);
		List<Property> properties = random.objects(Property.class, 3).collect(Collectors.toList());
		Map<String, String> dtos = new HashMap<>();
		for (Property p : properties) {
			dtos.put(p.getKey(), p.getValue());
		}
		when(propertyService.getAllByEntityId(id)).thenReturn(properties);
		when(propertyMapper.toDtos(properties)).thenReturn(dtos);
		Object response = controller.getPropertiesByEntityId(id, null);
		assertThat(response).isEqualTo(dtos);
	}

	@Test
	public void shouldCreateOrUpdateProperties() {
		String id = random.nextObject(String.class);
		Map<String, String> propertyMap = new HashMap<>();
		propertyMap.put("key1", "value1");
		doNothing().when(propertyService).createOrUpdate(id, propertyMap);
		controller.createOrUpdate(id, propertyMap);
		verify(propertyService).createOrUpdate(id, propertyMap);
	}

}
