    @Test
    public void journalYamlTest() {
        String MY_FUNCTION = "my.test.function";
        String ANOTHER_FUNCTION = "another.function";
        EventEmitter v0 = EventEmitter.getInstance();
        List<String> v1 = v0.getJournaledRoutes();
        Assert.assertEquals(2, v1.size());
        Assert.assertEquals(ANOTHER_FUNCTION, v1.get(0));
        Assert.assertEquals(MY_FUNCTION, v1.get(1));
    }