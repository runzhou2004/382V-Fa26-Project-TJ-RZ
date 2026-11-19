    @Test public void primitiveLongs() throws Exception {
        assertThat(testResult(PrimitiveLongs.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), PrimitiveLongs.iterations);
    }