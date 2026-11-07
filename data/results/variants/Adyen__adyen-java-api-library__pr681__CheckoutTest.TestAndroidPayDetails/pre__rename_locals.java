    @Test
    public void TestAndroidPayDetails() throws JsonProcessingException {
        String v0 = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"androidPayToken\":\"androidpaytoken\",\"type\":\"androidpay\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        AndroidPayDetails v1 = new AndroidPayDetails();
        v1.setAndroidPayToken("androidpaytoken");
        PaymentsRequest v2 = createPaymentsCheckoutRequest();
        v2.setPaymentMethod(v1);

        String v3 = GSON.toJson(v2);
        assertEquals(v0, v3);

        String v4 = OBJECT_MAPPER.writeValueAsString(v2);
        assertEquals(v0, v4);
    }