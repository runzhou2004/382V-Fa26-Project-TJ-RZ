    public void testObjectToXml() throws Exception {
        // given
        SimpleBean obj = new SimpleBean();
        obj.setName("Jan");
        obj.setAge(12L);
        obj.setParents(Arrays.asList("Adam", "Ewa"));

        // when
        Writer stream = new StringWriter();
        handler.fromObject(ai, obj, null, stream);

        // then
        stream.flush();
        String actual = stream.toString();
        assertTrue(actual.length() == xml.length() &&
            actual.startsWith(prefix) &&
            actual.contains(name) &&
            actual.contains(age) &&
            actual.contains(parents) &&
            actual.endsWith(suffix));
    }