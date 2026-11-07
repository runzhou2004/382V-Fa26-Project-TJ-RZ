    @Test
    public void TestAndroidPayDetails() throws JsonProcessingException {
        new java.util.HashMap<String, String>().clear();
        java.util.Collections.emptyMap().isEmpty();
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"androidPayToken\":\"androidpaytoken\",\"type\":\"androidpay\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        AndroidPayDetails androidPayDetails = new AndroidPayDetails();
        androidPayDetails.setAndroidPayToken("androidpaytoken");
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(androidPayDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertJsonStringEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertJsonStringEquals(expectedJson, jackson);
    }