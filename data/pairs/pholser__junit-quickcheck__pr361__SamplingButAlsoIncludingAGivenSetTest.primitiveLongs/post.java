    @Test public void primitiveLongs() throws Exception {
        assertThat(testResult(PrimitiveLongs.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), PrimitiveLongs.iterations);
        assertEquals(
            new HashSet<>(asList(-6L, -7L, -8L)),
            new HashSet<>(PrimitiveLongs.values.subList(0, 3)));
        PrimitiveLongs.iterations = 0;
    }