    @Test
    public void testDelete() {
        try {
            fixture.setDirectory(testResourcesDir);
            fixture.delete(copyFilename);
        } catch (SlimFixtureException sfe) {
            fail("Should not happen: " + sfe.getMessage());
        }
    }