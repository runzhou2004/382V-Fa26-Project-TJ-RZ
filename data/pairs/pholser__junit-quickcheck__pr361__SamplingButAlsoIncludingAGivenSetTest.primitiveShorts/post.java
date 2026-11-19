    @Test public void primitiveShorts() throws Exception {
        assertThat(testResult(PrimitiveShorts.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), PrimitiveShorts.iterations);
        assertEquals(
            new HashSet<>(asList(Short.valueOf("9"), Short.valueOf("8"))),
            new HashSet<>(PrimitiveShorts.values.subList(0, 2)));
        PrimitiveShorts.iterations = 0;
    }