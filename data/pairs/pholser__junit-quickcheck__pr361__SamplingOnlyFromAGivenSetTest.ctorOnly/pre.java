    @Test public void ctorOnly() throws Exception {
        assertThat(testResult(CtorOnly.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), CtorOnly.iterations);
    }