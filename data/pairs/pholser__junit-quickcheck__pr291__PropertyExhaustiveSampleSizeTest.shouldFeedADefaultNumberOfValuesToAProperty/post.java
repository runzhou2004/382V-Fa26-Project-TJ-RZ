    @Test public void shouldFeedADefaultNumberOfValuesToAProperty()
        throws Exception {

        assertThat(
            testResult(ForDefaultNumberOfValues.class),
            isSuccessful());
        assertEquals(
            defaultPropertyTrialCount(),
            ForDefaultNumberOfValues.iterations);
        ForDefaultNumberOfValues.iterations = 0;
    }