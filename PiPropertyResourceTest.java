package com.socgen.pad.obi.web.rest;

import static com.google.common.collect.ImmutableMap.of;
import static org.apache.commons.lang3.RandomStringUtils.randomAlphabetic;
import static org.assertj.core.api.Assertions.assertThat;
import static org.joda.time.DateTime.now;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import com.socgen.pad.obi.domain.service.*;
import com.socgen.pad.obi.web.mapper.AuditDtoMapper;
import com.socgen.pad.obi.web.mapper.PiDtoMapper;
import com.socgen.pad.obi.web.mapper.SummaryDtoMapper;
import org.jeasy.random.EasyRandom;
import org.jeasy.random.EasyRandomParameters;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;
import org.springframework.test.util.ReflectionTestUtils;

import com.socgen.pad.framework.domain.exception.FunctionalException;
import com.socgen.pad.framework.domain.model.PadUser;
import com.socgen.pad.framework.domain.service.impl.SgConnectHelper;
import com.socgen.pad.obi.domain.model.ObaPi;
import com.socgen.pad.obi.domain.model.Property;
import com.socgen.pad.obi.web.mapper.PropertyDtoMapper;

@RunWith(MockitoJUnitRunner.class)
public class PiPropertyResourceTest {

	@Mock
	private PiService service;
	@Mock
	private PropertyService propertyService;
	@Mock
	private SgConnectHelper sgConnectHelper;
	@Mock	
	private PropertyDtoMapper propertyMapper;
	@Mock
	private AuditDtoMapper auditDtoMapper;
	@Mock
	private PiDtoMapper piDtoMapper;
	@Mock
	private SummaryDtoMapper summaryDtoMapper;
	@Mock
	private MessagingService<ObaPi> messagingService;
	@Mock
	private ValidatorService validatorService;
    @Mock
	private PiSyncService piSyncService;

	private PiResource controller;
	private EasyRandom random;

	@Before
	public void setup() {
		random = new EasyRandom(new EasyRandomParameters()
				.seed(now().getMillis())
				.randomize(String.class, () -> randomAlphabetic(12)));
		// Manually instantiate controller with constructor dependencies
		controller = new PiResource(service, piDtoMapper, summaryDtoMapper, auditDtoMapper, messagingService,piSyncService);
		// Manually inject mocked dependencies into parent class fields
		ReflectionTestUtils.setField(controller, "propertyService", propertyService);
		ReflectionTestUtils.setField(controller, "propertyMapper", propertyMapper);
		ReflectionTestUtils.setField(controller, "sgConnectHelper", sgConnectHelper);
		ReflectionTestUtils.setField(controller, "validatorService", validatorService);
	}


	@Test
	public void shouldCreateOrUpdateProperties() {
		// Given
		String id = random.nextObject(String.class);
		Map<String, String> propertyMap = of(random.nextObject(String.class), random.nextObject(String.class));
		doNothing().when(propertyService).createOrUpdate(id, propertyMap);
		// When
		controller.createOrUpdate(id, propertyMap);
		// Then
		verify(propertyService).createOrUpdate(id, propertyMap);
	}

	@Test
	public void shouldReturnPropertyValueWhenGetByIdAndPropertyKey() throws FunctionalException {
		// Given
		String id = random.nextObject(String.class);
		String propertyKey = random.nextObject(String.class);
		String result = random.nextObject(String.class);
		when(propertyService.getValueByEntityIdAndKey(id, propertyKey)).thenReturn(result);
		// When
		Object value = controller.getPropertiesByEntityId(id, propertyKey);
		// Then
		assertThat(value).isEqualTo(result);
		verify(propertyService).getValueByEntityIdAndKey(id, propertyKey);
	}

	@Test
	public void shouldReturnPropertyMapWhenGetPropertiesById() throws FunctionalException {
		// Given
		String id = random.nextObject(String.class);
		List<Property> results = random.objects(Property.class, 5).collect(Collectors.toList());
		when(propertyService.getAllByEntityId(id)).thenReturn(results);
		when(propertyMapper.toDtos(results)).thenReturn(of("key", "value"));
		// When
		Object dto = controller.getPropertiesByEntityId(id, null);
		// Then
		assertThat(dto).isEqualTo(of("key", "value"));
		verify(propertyService).getAllByEntityId(id);
	}

}
