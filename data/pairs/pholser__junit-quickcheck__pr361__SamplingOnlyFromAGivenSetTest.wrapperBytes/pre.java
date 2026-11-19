    @Test public void wrapperBytes() throws Exception {
        assertThat(testResult(WrapperBytes.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), WrapperBytes.iterations);
    }