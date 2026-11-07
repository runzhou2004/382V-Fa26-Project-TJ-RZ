    @Test
    public void journalYamlTest() {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();
        String MY_FUNCTION = "my.test.function";
        String ANOTHER_FUNCTION = "another.function";
        EventEmitter po = EventEmitter.getInstance();
        List<String> routes = po.getJournaledRoutes();
        Assert.assertEquals(2, routes.size());
        Assert.assertTrue(routes.contains(ANOTHER_FUNCTION));
        Assert.assertTrue(routes.contains(MY_FUNCTION));
    }