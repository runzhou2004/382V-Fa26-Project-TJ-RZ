    @Test
    public void TestDateSerializers() throws ParseException {
        PaymentsRequest v0 = new PaymentsRequest();

        SimpleDateFormat v1 = new SimpleDateFormat("yyyy-MM-dd", Locale.ENGLISH);
        v1.setTimeZone(TimeZone.getTimeZone("GMT"));

        Date v2 = v1.parse("2018-10-31");
        v0.setDateOfBirth(v2);
        v0.setDeliveryDate(v2);
        String v3 = PRETTY_PRINT_GSON.toJson(v0);
        assertEquals("{\n"
                + "  \"dateOfBirth\": \"2018-10-31\",\n"
                + "  \"deliveryDate\": \"2018-10-31T00:00:00.000Z\",\n"
                + "  \"applicationInfo\": {\n"
                + "    \"adyenLibrary\": {\n"
                + "      \"name\": \"" + LIB_NAME + "\",\n"
                + "      \"version\": \"" + LIB_VERSION + "\"\n"
                + "    }\n"
                + "  }\n"
                + "}", v3);
    }