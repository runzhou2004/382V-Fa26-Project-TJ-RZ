    @Test
    public void toStringTest() {
        JSONObject rawSchemaJson = loader.readObj("tostring/objectschema.json");
        String actual = SchemaLoader.load(rawSchemaJson).toString();
        JSONAssert.assertEquals(rawSchemaJson.toString(), actual, false);
    }