    @Test public void wrapperIntegers() throws Exception {
        assertThat(testResult(WrapperIntegers.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), WrapperIntegers.iterations);
        assertEquals(
            new HashSet<>(asList(4, 5)),
            new HashSet<>(WrapperIntegers.values.subList(0, 2)));
        WrapperIntegers.iterations = 0;
    }