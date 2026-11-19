    @Test public void wrapperShorts() {
        assertThat(testResult(WrapperShorts.class), isSuccessful());
        assertEquals(2, WrapperShorts.iterations);
        assertEquals(
            new HashSet<>(asList(Short.valueOf("-13"), Short.valueOf("-14"))),
            WrapperShorts.testCases);
        WrapperShorts.iterations = 0;
        WrapperShorts.testCases.clear();
    }