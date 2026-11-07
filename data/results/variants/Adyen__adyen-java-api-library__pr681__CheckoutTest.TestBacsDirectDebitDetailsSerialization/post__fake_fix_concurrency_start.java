    @Test
    public void TestBacsDirectDebitDetailsSerialization() throws JsonProcessingException {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"GBP\"},\"merchantAccount\":\"TestMerchant\",\"paymentMethod\":{\"type\":\"directdebit_GB\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        BacsDirectDebitDetails bacsDirectDebitDetails = new BacsDirectDebitDetails();
        PaymentsRequest paymentsRequest = createBacsDirectDebitDetails();
        paymentsRequest.setPaymentMethod(bacsDirectDebitDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertJsonStringEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertJsonStringEquals(expectedJson, jackson);
    }