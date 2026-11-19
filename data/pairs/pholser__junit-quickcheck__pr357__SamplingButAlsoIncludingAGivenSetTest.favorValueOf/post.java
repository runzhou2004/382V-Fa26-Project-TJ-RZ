    @Test public void favorValueOf() throws Exception {
        assertThat(testResult(FavorValueOf.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), FavorValueOf.iterations);
        assertEquals(
            new HashSet<>(
                asList(
                    FavorValueOf.Target.valueOf("a"),
                    FavorValueOf.Target.valueOf("b"))),
            new HashSet<>(FavorValueOf.values.subList(0, 2)));
        FavorValueOf.iterations = 0;
    }