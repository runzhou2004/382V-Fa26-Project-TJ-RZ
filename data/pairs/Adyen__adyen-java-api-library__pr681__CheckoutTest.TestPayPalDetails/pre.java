    @Test
    public void TestPayPalDetails() throws JsonProcessingException {
        String expectedJson = "{\"amount\":{\"value\":1000,\"currency\":\"USD\"},\"merchantAccount\":\"MagentoMerchantTest\",\"paymentMethod\":{\"orderID\":\"orderId\",\"payerID\":\"payerId\",\"type\":\"paypal\",\"storedPaymentMethodId\":\"12345678\",\"subtype\":\"sdk\"},\"reference\":\"Your order number\",\"returnUrl\":\"https://your-company.com/...\",\"applicationInfo\":{\"adyenLibrary\":{\"name\":\"adyen-java-api-library\",\"version\":\"" + LIB_VERSION + "\"}}}";

        PayPalDetails payPalDetails = new PayPalDetails();
        payPalDetails.setOrderID("orderId");
        payPalDetails.setPayerID("payerId");
        payPalDetails.setSubtype(PayPalDetails.SubtypeEnum.SDK);
        payPalDetails.setStoredPaymentMethodId("12345678");
        PaymentsRequest paymentsRequest = createPaymentsCheckoutRequest();
        paymentsRequest.setPaymentMethod(payPalDetails);

        String gson = GSON.toJson(paymentsRequest);
        assertEquals(expectedJson, gson);

        String jackson = OBJECT_MAPPER.writeValueAsString(paymentsRequest);
        assertEquals(expectedJson, jackson);
    }