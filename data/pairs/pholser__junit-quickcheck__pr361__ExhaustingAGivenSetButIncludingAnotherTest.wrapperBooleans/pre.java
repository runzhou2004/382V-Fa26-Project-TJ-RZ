    @Test public void wrapperBooleans() throws Exception {
        assertThat(testResult(WrapperBooleans.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), WrapperBooleans.iterations);
        assertEquals(
            singletonList(false),
            WrapperBooleans.values.subList(0, 1));
    }