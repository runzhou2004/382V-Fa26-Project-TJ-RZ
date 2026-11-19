    @Test public void strings() {
        assertThat(testResult(Strings.class), isSuccessful());
        assertEquals(2, Strings.iterations);
        assertEquals(
            new HashSet<>(asList("some", "values")),
            Strings.testCases);
    }