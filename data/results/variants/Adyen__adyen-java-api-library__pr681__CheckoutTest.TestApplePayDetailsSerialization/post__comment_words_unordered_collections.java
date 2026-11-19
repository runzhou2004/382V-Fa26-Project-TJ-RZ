    @Test
    public void TestApplePayDetailsSerialization() throws JsonProcessingException {
        // iteration order of HashMap or HashSet, sorted output
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"applePayToken\":\"applepaytoken\",\"fundingSource\":\"credit\",\"type\":\"applepay\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        ApplePayDetails applePayDetails = new ApplePayDetails();
        applePayDetails.setApplePayToken("applepaytoken");
        applePayDetails.setFundingSource(ApplePayDetails.FundingSourceEnum.CREDIT);
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(applePayDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertJsonStringEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertJsonStringEquals(expectedJson, jackson);
    }