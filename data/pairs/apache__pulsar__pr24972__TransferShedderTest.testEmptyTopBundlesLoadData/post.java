    @Test
    public void testEmptyTopBundlesLoadData() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = getContext();
        var brokerLoadDataStore = ctx.brokerLoadDataStore();

        brokerLoadDataStore.pushAsync("broker1:8080", getCpuLoad(ctx, 2, "broker1:8080"));
        brokerLoadDataStore.pushAsync("broker2:8080", getCpuLoad(ctx, 4, "broker2:8080"));
        brokerLoadDataStore.pushAsync("broker3:8080", getCpuLoad(ctx, 6, "broker3:8080"));
        brokerLoadDataStore.pushAsync("broker4:8080", getCpuLoad(ctx, 80, "broker4:8080"));
        brokerLoadDataStore.pushAsync("broker5:8080", getCpuLoad(ctx, 90, "broker5:8080"));


        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoLoadData).get(), 1);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);
    }