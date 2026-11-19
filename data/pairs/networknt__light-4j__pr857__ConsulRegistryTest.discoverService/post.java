    @Test
    public void discoverService() throws Exception {
        registry.doRegister(serviceUrl);
        List<URL> urls = registry.discover(serviceUrl);
        Assert.assertEquals(0, urls.size());

        registry.doAvailable(null);
        Thread.sleep(sleepTime);
        urls = registry.discover(serviceUrl);
        Assert.assertTrue(urls.contains(serviceUrl));
        
        // unavailable
        registry.doUnavailable(null);
        Thread.sleep(sleepTime);
        Assert.assertFalse(client.isWorking(serviceid));
    }