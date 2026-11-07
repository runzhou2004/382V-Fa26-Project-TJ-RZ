    @Test
    public void TestBlikDetailsSerialization() throws JsonProcessingException {
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"blikCode\":\"blikCode\",\"type\":\"blik\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}"; // ok

        BlikDetails blikDetails = new BlikDetails();
        blikDetails.setBlikCode("blikCode");
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(blikDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertEquals(expectedJson, jackson);
    }