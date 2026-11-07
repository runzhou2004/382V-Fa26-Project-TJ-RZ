    @Test
    public void TestBacsDirectDebitDetailsSerialization() throws JsonProcessingException {
        String v0 = "{\"amount\":{\"value\":1000,\"currency\":\"GBP\"},\"merchantAccount\":\"TestMerchant\",\"paymentMethod\":{\"type\":\"directdebit_GB\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        BacsDirectDebitDetails v1 = new BacsDirectDebitDetails();
        PaymentsRequest v2 = createBacsDirectDebitDetails();
        v2.setPaymentMethod(v1);

        String v3 = GSON.toJson(v2);
        assertEquals(v0, v3);

        String v4 = OBJECT_MAPPER.writeValueAsString(v2);
        assertEquals(v0, v4);
    }