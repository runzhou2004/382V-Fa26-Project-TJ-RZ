    @Test
    public void testBuildLockKeys() throws Exception {
        connectionContext.appendLockKey("abc");
        connectionContext.appendLockKey("bcd");

        Assertions.assertTrue(connectionContext.hasLockKey());
        Assertions.assertEquals(connectionContext.buildLockKeys(), "bcd;abc");
    }