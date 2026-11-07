    @Test
    public void TestBacsDirectDebitDetailsSerialization() throws JsonProcessingException {
        // reviewed
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"GBP\"},\"merchantAccount\":\"TestMerchant\",\"paymentMethod\":{\"type\":\"directdebit_GB\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        BacsDirectDebitDetails bacsDirectDebitDetails = new BacsDirectDebitDetails();
        PaymentsRequest paymentsRequest = createBacsDirectDebitDetails();
        paymentsRequest.setPaymentMethod(bacsDirectDebitDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertEquals(expectedJson, jackson);
    }