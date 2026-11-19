    @Test public void expectedOrderingOfMethods() throws Exception {
        assertThat(testResult(Leaf.class), isSuccessful());
        assertEquals(
            resourceAsString("trait-property-test-expected.txt"),
            bytesOut.toString());
    }