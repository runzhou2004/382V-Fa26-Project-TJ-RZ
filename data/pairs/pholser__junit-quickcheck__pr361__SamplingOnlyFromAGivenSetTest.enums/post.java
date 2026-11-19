    @Test public void enums() throws Exception {
        assertThat(testResult(Enums.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), Enums.iterations);
        Enums.iterations = 0;
    }