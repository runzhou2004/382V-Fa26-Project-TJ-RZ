    @Test public void primitiveIntegers() throws Exception {
        assertThat(testResult(PrimitiveIntegers.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), PrimitiveIntegers.iterations);
        assertEquals(
            new HashSet<>(asList(1, 2, 3)),
            new HashSet<>(PrimitiveIntegers.values.subList(0, 3)));
        PrimitiveIntegers.iterations = 0;
    }