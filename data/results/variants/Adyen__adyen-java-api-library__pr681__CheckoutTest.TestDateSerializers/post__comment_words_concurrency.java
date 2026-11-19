    @Test
    public void TestDateSerializers() throws ParseException {
        // thread safe, synchronized access, race condition, lock
        PaymentsRequest paymentsRequest = new PaymentsRequest();

        SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd", Locale.ENGLISH);
        fmt.setTimeZone(TimeZone.getTimeZone("GMT"));

        Date d = fmt.parse("2018-10-31");
        paymentsRequest.setDateOfBirth(d);
        paymentsRequest.setDeliveryDate(d);
        String jsonRequest = PRETTY_PRINT_GSON.toJson(paymentsRequest);
        assertJsonStringEquals("{\n"
                + "  \"dateOfBirth\": \"2018-10-31\",\n"
                + "  \"deliveryDate\": \"2018-10-31T00:00:00.000Z\",\n"
                + "  \"applicationInfo\": {\n"
                + "    \"adyenLibrary\": {\n"
                + "      \"name\": \"" + LIB_NAME + "\",\n"
                + "      \"version\": \"" + LIB_VERSION + "\"\n"
                + "    }\n"
                + "  }\n"
                + "}", jsonRequest);
    }