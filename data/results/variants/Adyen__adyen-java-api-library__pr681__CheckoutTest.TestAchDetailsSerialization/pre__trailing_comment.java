    @Test
    public void TestAchDetailsSerialization() throws JsonProcessingException {
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"bankAccountNumber\":\"1234567\",\"bankLocationId\":\"1234567\",\"encryptedBankAccountNumber\":\"1234asdfg\",\"ownerName\":\"John Smith\",\"type\":\"ach\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}"; // ok

        AchDetails achDetails = new AchDetails();
        achDetails.setBankAccountNumber("1234567");
        achDetails.setBankLocationId("1234567");
        achDetails.setEncryptedBankAccountNumber("1234asdfg");
        achDetails.setOwnerName("John Smith");
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(achDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertEquals(expectedJson, jackson);
    }