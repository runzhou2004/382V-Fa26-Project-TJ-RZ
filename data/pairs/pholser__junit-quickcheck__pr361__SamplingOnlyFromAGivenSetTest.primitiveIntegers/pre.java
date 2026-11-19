    @Test public void primitiveIntegers() throws Exception {
        assertThat(testResult(PrimitiveIntegers.class), isSuccessful());
        assertEquals(
            defaultPropertyTrialCount(),
            PrimitiveIntegers.iterations);
    }