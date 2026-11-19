    @Test public void wrapperLongs() {
        assertThat(testResult(WrapperLongs.class), isSuccessful());
        assertEquals(3, WrapperLongs.iterations);
        assertEquals(
            new HashSet<>(asList(10L, 11L, 12L)),
            WrapperLongs.testCases);
    }