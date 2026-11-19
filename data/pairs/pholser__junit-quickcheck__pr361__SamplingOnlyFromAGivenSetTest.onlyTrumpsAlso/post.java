    @Test public void onlyTrumpsAlso() throws Exception {
        assertThat(testResult(OnlyTrumpsAlso.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), OnlyTrumpsAlso.iterations);
        OnlyTrumpsAlso.iterations = 0;
    }