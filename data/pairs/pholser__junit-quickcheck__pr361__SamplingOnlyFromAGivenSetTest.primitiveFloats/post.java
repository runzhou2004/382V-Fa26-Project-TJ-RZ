    @Test public void primitiveFloats() throws Exception {
        assertThat(testResult(PrimitiveFloats.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), PrimitiveFloats.iterations);
        PrimitiveFloats.iterations = 0;
    }