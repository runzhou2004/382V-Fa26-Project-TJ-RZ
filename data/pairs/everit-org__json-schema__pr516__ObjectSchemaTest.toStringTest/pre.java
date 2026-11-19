    @Test
    public void toStringTest() {
        JSONObject rawSchemaJson = loader.readObj("tostring/objectschema.json");
        String actual = SchemaLoader.load(rawSchemaJson).toString();
        assertThat(new JSONObject(actual), sameJsonAs(rawSchemaJson));
    }