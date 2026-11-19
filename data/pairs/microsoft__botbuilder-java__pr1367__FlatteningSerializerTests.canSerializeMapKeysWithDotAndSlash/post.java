    @Test
    public void canSerializeMapKeysWithDotAndSlash() throws Exception {
        String serialized = new JacksonAdapter().serialize(prepareSchoolModel());
        String expected = "{\"teacher\":{\"students\":{\"af.B/D\":{},\"af.B/C\":{}}},\"tags\":{\"foo.aa\":\"bar\",\"x.y\":\"zz\"},\"properties\":{\"name\":\"school1\"}}";
        assertJsonEqualsNonStrict(expected, serialized);
    }