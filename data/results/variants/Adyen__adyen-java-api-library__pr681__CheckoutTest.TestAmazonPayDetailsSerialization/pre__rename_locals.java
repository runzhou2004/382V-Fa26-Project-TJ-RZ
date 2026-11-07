    @Test
    public void TestAmazonPayDetailsSerialization() throws JsonProcessingException {
        String v0 = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"amazonPayToken\":\"amazonpaytoken\",\"checkoutSessionId\":\"checkoutsessionid\",\"type\":\"amazonpay\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        AmazonPayDetails v1 = new AmazonPayDetails();
        v1.setAmazonPayToken("amazonpaytoken");
        v1.setCheckoutSessionId("checkoutsessionid");

        PaymentsRequest v2 = createPaymentsCheckoutRequest();
        v2.setPaymentMethod(v1);

        String v3 = GSON.toJson(v2);
        assertEquals(v0, v3);

        String v4 = OBJECT_MAPPER.writeValueAsString(v2);
        assertEquals(v0, v4);
    }