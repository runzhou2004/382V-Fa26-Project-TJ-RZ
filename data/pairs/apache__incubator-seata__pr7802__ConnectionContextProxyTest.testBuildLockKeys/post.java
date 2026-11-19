    @Test
    public void testBuildLockKeys() throws Exception {
        connectionContext.appendLockKey("abc");
        connectionContext.appendLockKey("bcd");

        Assertions.assertTrue(connectionContext.hasLockKey());

        assertLockKeysEqual("abc;bcd", connectionContext.buildLockKeys());
    }