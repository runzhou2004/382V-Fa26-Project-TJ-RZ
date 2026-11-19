    @Test public void primitiveChars() throws Exception {
        assertThat(testResult(PrimitiveChars.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), PrimitiveChars.iterations);
    }