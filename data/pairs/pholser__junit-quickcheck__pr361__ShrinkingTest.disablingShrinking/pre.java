    @Test public void disablingShrinking() {
        assertThat(testResult(DisablingShrinking.class), failureCountIs(1));
        assertEquals(1, DisablingShrinking.attempts.size());
    }