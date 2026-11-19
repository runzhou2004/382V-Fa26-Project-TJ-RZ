    @Test public void primitiveBytes() {
        assertThat(testResult(PrimitiveBytes.class), isSuccessful());
        assertEquals(2, PrimitiveBytes.iterations);
        assertEquals(
            new HashSet<>(asList(Byte.valueOf("12"), Byte.valueOf("-13"))),
            PrimitiveBytes.testCases);
        PrimitiveBytes.iterations = 0;
    }