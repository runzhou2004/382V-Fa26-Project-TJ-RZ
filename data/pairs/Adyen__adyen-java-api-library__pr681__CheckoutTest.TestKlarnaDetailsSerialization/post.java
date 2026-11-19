    @Test
    public void TestKlarnaDetailsSerialization() throws JsonProcessingException {
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"bankAccount\":\"bankaccount\",\"billingAddress\":\"billingaddress\",\"deliveryAddress\":\"deliveryaddress\",\"installmentConfigurationKey\":\"installmentconfigurationkey\",\"personalDetails\":\"personaldetails\",\"separateDeliveryAddress\":\"separatedeliveryaddress\",\"storedPaymentMethodId\":\"storedpaymentmethodid\",\"token\":\"token\",\"type\":\"klarna\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        KlarnaDetails klarnaDetails = new KlarnaDetails();
        klarnaDetails.setBankAccount("bankaccount");
        klarnaDetails.setBillingAddress("billingaddress");
        klarnaDetails.setDeliveryAddress("deliveryaddress");
        klarnaDetails.setInstallmentConfigurationKey("installmentconfigurationkey");
        klarnaDetails.setPersonalDetails("personaldetails");
        klarnaDetails.setSeparateDeliveryAddress("separatedeliveryaddress");
        klarnaDetails.setStoredPaymentMethodId("storedpaymentmethodid");
        klarnaDetails.setToken("token");
        klarnaDetails.setType(KlarnaDetails.KLARNA);
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(klarnaDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertJsonStringEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertJsonStringEquals(expectedJson, jackson);
    }