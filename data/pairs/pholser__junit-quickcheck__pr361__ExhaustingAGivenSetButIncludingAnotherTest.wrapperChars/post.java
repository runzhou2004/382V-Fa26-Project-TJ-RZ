    @Test public void wrapperChars() {
        assertThat(testResult(WrapperChars.class), isSuccessful());
        assertEquals(23, WrapperChars.iterations);
        assertEquals(
            new HashSet<>(asList('@', '#')),
            new HashSet<>(WrapperChars.values.subList(0, 2)));
        WrapperChars.iterations = 0;
    }