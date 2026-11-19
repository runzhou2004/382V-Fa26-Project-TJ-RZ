    @Test
    public void testMinBrokerWithLowerLoadThanAvg() throws IllegalAccessException {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        var brokerLoadDataStore = ctx.brokerLoadDataStore();

        var load = getCpuLoad(ctx,  3 , "broker2:8080");
        brokerLoadDataStore.pushAsync("broker2:8080", load);
        brokerLoadDataStore.pushAsync("broker4:8080", getCpuLoad(ctx,  55, "broker4:8080"));
        brokerLoadDataStore.pushAsync("broker5:8080", getCpuLoad(ctx,  65, "broker5:8080"));

        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());

        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.of("broker2:8080")),
                Success, Underloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), 0.262, delta);
        assertEquals(counter.getLoadStd(), 0.2780935094532054, delta);
    }