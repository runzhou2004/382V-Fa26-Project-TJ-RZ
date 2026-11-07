    // shared static state, depends on test execution order
    @Test
    public void journalYamlTest() {
        String MY_FUNCTION = "my.test.function";
        String ANOTHER_FUNCTION = "another.function";
        EventEmitter po = EventEmitter.getInstance();
        List<String> routes = po.getJournaledRoutes();
        Assert.assertEquals(2, routes.size());
        Assert.assertEquals(ANOTHER_FUNCTION, routes.get(0));
        Assert.assertEquals(MY_FUNCTION, routes.get(1));
    }