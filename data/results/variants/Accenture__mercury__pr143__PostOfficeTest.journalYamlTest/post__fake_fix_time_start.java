    @Test
    public void journalYamlTest() {
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);
        String MY_FUNCTION = "my.test.function";
        String ANOTHER_FUNCTION = "another.function";
        EventEmitter po = EventEmitter.getInstance();
        List<String> routes = po.getJournaledRoutes();
        Assert.assertEquals(2, routes.size());
        Assert.assertTrue(routes.contains(ANOTHER_FUNCTION));
        Assert.assertTrue(routes.contains(MY_FUNCTION));
    }