    @Test
    public void testZeroBundleThroughput() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        var topBundlesLoadDataStore = ctx.topBundleLoadDataStore();
        for (var e : topBundlesLoadDataStore.entrySet()) {
            for (var stat : e.getValue().getTopBundlesLoadData()) {
                stat.stats().msgThroughputOut = 0;
                stat.stats().msgThroughputIn = 0;

            }
        }
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoBundles).get(), 1);
        assertEquals(counter.getLoadAvg(), setupLoadAvg);
        assertEquals(counter.getLoadStd(), setupLoadStd);
    }