    @Test public void acrossParametersOfSameParameterizedTypeWithOneConstant()
        throws Exception {

        assertThat(
            testResult(ParametersOfSameParameterizedTypeWithOneConstant.class),
            isSuccessful());
        assertEquals(
            defaultPropertyTrialCount(),
            ParametersOfSameParameterizedTypeWithOneConstant.iterations);
    }