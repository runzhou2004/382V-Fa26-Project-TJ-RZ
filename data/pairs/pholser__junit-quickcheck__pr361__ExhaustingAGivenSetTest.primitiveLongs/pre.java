    @Test public void primitiveLongs() {
        assertThat(testResult(PrimitiveLongs.class), isSuccessful());
        assertEquals(3, PrimitiveLongs.iterations);
        assertEquals(
            new HashSet<>(asList(-6L, -7L, -8L)),
            PrimitiveLongs.testCases);
    }