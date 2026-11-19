    @Test public void manyParametersWithBooleanAndEnum() {
        assertThat(
            testResult(ManyParametersWithBooleanAndEnum.class),
            isSuccessful());

        assertEquals(
            2 * 5 * 2 * RoundingMode.values().length,
            ManyParametersWithBooleanAndEnum.iterations);
        assertEquals(
            newHashSet(3, 7),
            new HashSet<>(ManyParametersWithBooleanAndEnum.firstTestCases));
        assertEquals(
            newHashSet('a', 'b', 'c', 'd', 'e'),
            new HashSet<>(ManyParametersWithBooleanAndEnum.secondTestCases));
        assertEquals(
            newHashSet(false, true),
            new HashSet<>(ManyParametersWithBooleanAndEnum.thirdTestCases));
        assertEquals(
            EnumSet.allOf(RoundingMode.class),
            new HashSet<>(ManyParametersWithBooleanAndEnum.fourthTestCases));
        ManyParametersWithBooleanAndEnum.iterations = 0;
        ManyParametersWithBooleanAndEnum.firstTestCases.clear();
        ManyParametersWithBooleanAndEnum.secondTestCases.clear();
        ManyParametersWithBooleanAndEnum.thirdTestCases.clear();
        ManyParametersWithBooleanAndEnum.fourthTestCases.clear();
    }