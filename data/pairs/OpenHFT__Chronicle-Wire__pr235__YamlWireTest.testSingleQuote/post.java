    @Test
    public void testSingleQuote() {
        ClassAliasPool.CLASS_ALIASES.addAlias(YNestedA.class);
        YNestedA a = Marshallable.fromString("!YNestedA {\n" +
                "  b: !YNestedB,\n" +
                "  value: 12345\n" +
                "}");
        assertNotNull(a);
    }