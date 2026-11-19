    @Test public void explicitConversion() {
        assertThat(testResult(ExplicitConversion.class), isSuccessful());
        assertEquals(2, ExplicitConversion.iterations);
        assertEquals(
            new HashSet<>(asList(
                LocalDate.of(2017, 1, 1),
                LocalDate.of(2001, 12, 25))),
            ExplicitConversion.testCases
        );
        ExplicitConversion.iterations = 0;
        ExplicitConversion.testCases.clear();
    }