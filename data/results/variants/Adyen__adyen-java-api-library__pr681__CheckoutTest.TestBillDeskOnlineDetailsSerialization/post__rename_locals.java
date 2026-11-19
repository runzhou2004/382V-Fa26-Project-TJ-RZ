    @Test
    public void TestBillDeskOnlineDetailsSerialization() throws JsonProcessingException {
        String v0 = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"issuer\":\"111\",\"type\":\"billdesk_online\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        BillDeskOnlineDetails v1 = new BillDeskOnlineDetails();
        v1.setIssuer("111");
        PaymentsRequest v2 = createPaymentsCheckoutRequest();
        v2.setPaymentMethod(v1);

        String v3 = GSON.toJson(v2);
        assertJsonStringEquals(v0, v3);

        String v4 = OBJECT_MAPPER.writeValueAsString(v2);
        assertJsonStringEquals(v0, v4);
    }