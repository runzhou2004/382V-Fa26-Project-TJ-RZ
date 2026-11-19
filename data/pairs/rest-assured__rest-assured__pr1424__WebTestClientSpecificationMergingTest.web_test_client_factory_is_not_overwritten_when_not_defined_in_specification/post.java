	web_test_client_factory_is_not_overwritten_when_not_defined_in_specification() {
		// Given
		RestAssuredWebTestClient.reset();
		WebTestClient webTestClientInstance = WebTestClient.bindToController(new GreetingController()).build();
		WebTestClientRequestSpecification specToMerge = new WebTestClientRequestSpecBuilder().addQueryParam("param1", "value1").build();

		// When
		WebTestClientRequestSpecification spec = RestAssuredWebTestClient.given().webTestClient(webTestClientInstance).spec(specToMerge);

		// Then
		WebTestClient webTestClient = Whitebox.getInternalState(implementation(spec).getWebTestClientFactory(),
				"webTestClient");
		assertThat(webTestClient).isSameAs(webTestClientInstance);
		Assertions.assertThat(implementation(spec).getQueryParams()).containsOnly(entry("param1", "value1"));
	}