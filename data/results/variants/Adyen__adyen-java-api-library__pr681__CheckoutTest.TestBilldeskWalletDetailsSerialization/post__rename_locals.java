    @Test
    public void TestBilldeskWalletDetailsSerialization() throws JsonProcessingException {
        String v0 = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"issuer\":\"111\",\"type\":\"billdesk_wallet\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        BillDeskWalletDetails v1 = new BillDeskWalletDetails();
        v1.setIssuer("111");
        PaymentsRequest v2 = createPaymentsCheckoutRequest();
        v2.setPaymentMethod(v1);

        String v3 = GSON.toJson(v2);
        assertJsonStringEquals(v0, v3);

        String v4 = OBJECT_MAPPER.writeValueAsString(v2);
        assertJsonStringEquals(v0, v4);
    }