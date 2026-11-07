    @Test
    public void TestBillDeskOnlineDetailsSerialization() throws JsonProcessingException {
        // shared static state, depends on test execution order
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"issuer\":\"111\",\"type\":\"billdesk_online\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        BillDeskOnlineDetails billdeskOnlineDetails = new BillDeskOnlineDetails();
        billdeskOnlineDetails.setIssuer("111");
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(billdeskOnlineDetails);

        String gsonRequest = GSON.toJson(paymentsRequest);
        assertJsonStringEquals(expectedJson, gsonRequest);

        String jacksonRequest = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertJsonStringEquals(expectedJson, jacksonRequest);
    }