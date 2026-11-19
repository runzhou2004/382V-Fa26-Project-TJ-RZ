    public void testTwoAttributes() throws IOException
    {
        XmlMapper mapper = XmlMapper.builder()
                .annotationIntrospector(jakartaXMLBindAnnotationIntrospector())
                .build();
        String xml = mapper.writeValueAsString(new Jurisdiction());
        assertEquals("<Jurisdiction name=\"Foo\" value=\"13\"/>", xml);
    }