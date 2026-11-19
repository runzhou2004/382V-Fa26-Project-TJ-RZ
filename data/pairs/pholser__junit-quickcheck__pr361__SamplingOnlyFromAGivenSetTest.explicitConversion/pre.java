    @Test public void explicitConversion() throws Exception {
        assertThat(testResult(ExplicitConversion.class), isSuccessful());
        assertEquals(
            defaultPropertyTrialCount(),
            ExplicitConversion.iterations);
    }