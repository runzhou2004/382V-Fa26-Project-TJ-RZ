    @Test public void orderingOfStatements() {
        assertThat(testResult(PropertyBasedTests.class), failureCountIs(1));
        assertEquals(expectedStatements, PropertyBasedTests.LOGS);
    }