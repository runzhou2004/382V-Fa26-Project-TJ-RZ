    @Test
    public void testDelete() {
        try {
            fixture.setDirectory(testResourcesDir);
            fixture.copyTo(txtFilename, copyFilename);
            fixture.delete(copyFilename);
        } catch (Exception ex) {
            fail("Should not happen: " + ex.getMessage());
        }
    }