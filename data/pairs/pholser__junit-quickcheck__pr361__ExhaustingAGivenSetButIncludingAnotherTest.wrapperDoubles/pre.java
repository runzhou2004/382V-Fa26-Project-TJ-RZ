    @Test public void wrapperDoubles() throws Exception {
        assertThat(testResult(WrapperDoubles.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), WrapperDoubles.iterations);
        assertEquals(
            new HashSet<>(asList(2.7, -3.14)),
            new HashSet<>(WrapperDoubles.values.subList(0, 2)));
    }