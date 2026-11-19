    @Test
    public void canSerializeMapKeysWithDotAndSlash() throws Exception {
        String serialized = new JacksonAdapter().serialize(prepareSchoolModel());
        Assert.assertEquals("{\"teacher\":{\"students\":{\"af.B/D\":{},\"af.B/C\":{}}},\"tags\":{\"foo.aa\":\"bar\",\"x.y\":\"zz\"},\"properties\":{\"name\":\"school1\"}}", serialized);
    }