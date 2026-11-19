    @Test
    public void testSingleQuote() {
        YNestedA a = Marshallable.fromString("!YNestedA {\n" +
                "  b: !YNestedB,\n" +
                "  value: 12345\n" +
                "}");
        assertNotNull(a);
    }