    @Test
    public void testTargetStdAfterTransfer() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        var brokerLoadDataStore = ctx.brokerLoadDataStore();
        brokerLoadDataStore.pushAsync("broker4:8080", getCpuLoad(ctx,  55, "broker4:8080"));
        brokerLoadDataStore.pushAsync("broker5:8080", getCpuLoad(ctx,  65, "broker5:8080"));
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());

        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), 0.26400000000000007);
        assertEquals(counter.getLoadStd(), 0.27644891028904417);
    }