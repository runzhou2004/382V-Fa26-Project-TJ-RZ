  @Test
  public void TestAmazonPayDetailsSerialization() throws JsonProcessingException {
    String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"amazonPayToken\":\"amazonpaytoken\",\"checkoutSessionId\":\"checkoutsessionid\",\"type\":\"amazonpay\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

    AmazonPayDetails amazonPayDetails = new AmazonPayDetails();
    amazonPayDetails.setAmazonPayToken("amazonpaytoken");
    amazonPayDetails.setCheckoutSessionId("checkoutsessionid");

    PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
    paymentsRequest.setPaymentMethod(amazonPayDetails);

    String gson = GSON.toJson(paymentsRequest);
    assertJsonStringEquals(expectedJson, gson);

    String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
    assertJsonStringEquals(expectedJson, jackson);
  }