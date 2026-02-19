package com.socgen.pad.obi.web.rest.swagger;

import static org.apache.commons.lang3.RandomStringUtils.randomAlphabetic;
import static org.assertj.core.api.Assertions.assertThat;
import static org.joda.time.DateTime.now;

import org.jeasy.random.EasyRandom;
import org.jeasy.random.EasyRandomParameters;
import org.junit.Before;
import org.junit.Test;

import com.socgen.pad.framework.domain.model.ResponseData;

public class SwaggerResponsesTest {

	private EasyRandom random;

	@Before
	public void setUp() {
		random = new EasyRandom(new EasyRandomParameters()
				.seed(now().getMillis())
				.randomize(String.class, () -> randomAlphabetic(12)));
	}

	@Test
	public void shouldPiListResponseExtendFromResponseData() {
		// When
		SwaggerResponses.PiListResponse response = random.nextObject(SwaggerResponses.PiListResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldPiResponseExtendFromResponseData() {
		// When
		SwaggerResponses.PiResponse response = random.nextObject(SwaggerResponses.PiResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldObaListResponseExtendFromResponseData() {
		// When
		SwaggerResponses.ObaListResponse response = random.nextObject(SwaggerResponses.ObaListResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldObaResponseExtendFromResponseData() {
		// When
		SwaggerResponses.ObaResponse response = random.nextObject(SwaggerResponses.ObaResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldReturnObaSummaryExtendFromResponseData() {
		// When
		SwaggerResponses.ObaSummaryListResponse response = random.nextObject(SwaggerResponses.ObaSummaryListResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldReturnAuditListResponseExtendFromResponseData() {
		// When
		SwaggerResponses.AuditListResponse response = random.nextObject(SwaggerResponses.AuditListResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldReturnPiSummaryListExtendFromResponseData() {
		// When
		SwaggerResponses.PiSummaryListResponse response = random.nextObject(SwaggerResponses.PiSummaryListResponse.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldReturnJobResultDataExtendFromResponseData() {
		// When
		SwaggerResponses.JobResultData response = random.nextObject(SwaggerResponses.JobResultData.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

	@Test
	public void shouldReturnRequesterLiteDataExtendFromResponseData() {
		// When
		SwaggerResponses.RequesterLiteData response = random.nextObject(SwaggerResponses.RequesterLiteData.class);
		// Then
		assertThat(response.getClass().getSuperclass()).isEqualTo(ResponseData.class);
	}

}
