    @Test public void strings() throws Exception {
        assertThat(testResult(Strings.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), Strings.iterations);
        assertEquals(
            new HashSet<>(asList("some", "values")),
            new HashSet<>(Strings.values.subList(0, 2)));
        Strings.iterations = 0;
    }