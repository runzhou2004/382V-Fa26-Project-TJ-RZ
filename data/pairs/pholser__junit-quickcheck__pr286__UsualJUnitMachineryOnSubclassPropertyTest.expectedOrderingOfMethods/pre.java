    @Test public void expectedOrderingOfMethods() throws Exception {
        assertThat(testResult(Leaf.class), isSuccessful());
        assertEquals(
            resourceAsString("subclass-property-test-expected.txt"),
            bytesOut.toString());
    }