    @Test public void manyParameters() {
        assertThat(testResult(ManyParameters.class), isSuccessful());
        assertEquals(10, ManyParameters.iterations);
        assertEquals(
            new HashSet<>(asList(-1, -2, -4)),
            new HashSet<>(ManyParameters.firstValues.subList(0, 3)));
        assertEquals(
            new HashSet<>(asList('r', 'y')),
            new HashSet<>(ManyParameters.secondValues.subList(0, 2)));
    }