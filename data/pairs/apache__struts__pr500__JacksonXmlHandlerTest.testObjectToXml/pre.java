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
        assertEquals(xml, stream.toString());
    }