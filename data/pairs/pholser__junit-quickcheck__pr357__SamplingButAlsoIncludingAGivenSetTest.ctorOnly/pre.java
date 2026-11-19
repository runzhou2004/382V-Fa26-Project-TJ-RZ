    @Test public void ctorOnly() throws Exception {
        assertThat(testResult(CtorOnly.class), isSuccessful());
        assertEquals(defaultPropertyTrialCount(), CtorOnly.iterations);
        assertEquals(
            new HashSet<>(
                asList(new CtorOnly.Target("a"), new CtorOnly.Target("b"))),
            new HashSet<>(CtorOnly.values.subList(0, 2)));
    }