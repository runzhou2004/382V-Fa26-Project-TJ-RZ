    @Test
    public void TestAchDetailsSerialization() throws JsonProcessingException {
        String v0 = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"bankAccountNumber\":\"1234567\",\"bankLocationId\":\"1234567\",\"encryptedBankAccountNumber\":\"1234asdfg\",\"ownerName\":\"John Smith\",\"type\":\"ach\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        AchDetails v1 = new AchDetails();
        v1.setBankAccountNumber("1234567");
        v1.setBankLocationId("1234567");
        v1.setEncryptedBankAccountNumber("1234asdfg");
        v1.setOwnerName("John Smith");
        PaymentsRequest v2 = createPaymentsCheckoutRequest();
        v2.setPaymentMethod(v1);

        String v3 = GSON.toJson(v2);
        assertEquals(v0, v3);

        String v4 = OBJECT_MAPPER.writeValueAsString(v2);
        assertEquals(v0, v4);
    }