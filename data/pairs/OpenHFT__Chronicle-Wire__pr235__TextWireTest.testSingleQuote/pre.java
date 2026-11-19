    @Test
    public void testSingleQuote() {
        NestedA a = Marshallable.fromString("!NestedA {\n" +
                "  b: !NestedB,\n" +
                "  value: 12345\n" +
                "}");
        assertNotNull(a);
    }