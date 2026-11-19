    @Test
    public void testSingleTopBundlesLoadData() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        var topBundlesLoadDataStore = ctx.topBundleLoadDataStore();
        topBundlesLoadDataStore.pushAsync("broker1:8080", getTopBundlesLoad("my-tenant/my-namespaceA", 1));
        topBundlesLoadDataStore.pushAsync("broker2:8080", getTopBundlesLoad("my-tenant/my-namespaceB", 2));
        topBundlesLoadDataStore.pushAsync("broker3:8080", getTopBundlesLoad("my-tenant/my-namespaceC", 6));
        topBundlesLoadDataStore.pushAsync("broker4:8080", getTopBundlesLoad("my-tenant/my-namespaceD", 10));
        topBundlesLoadDataStore.pushAsync("broker5:8080", getTopBundlesLoad("my-tenant/my-namespaceE", 70));
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());

        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoBundles).get(), 1);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);
    }