    @Test
    public void testSingleQuote() {
        ClassAliasPool.CLASS_ALIASES.addAlias(NestedA.class);
        NestedA a = Marshallable.fromString("!NestedA {\n" +
                "  b: !NestedB,\n" +
                "  value: 12345\n" +
                "}");
        assertNotNull(a);
    }