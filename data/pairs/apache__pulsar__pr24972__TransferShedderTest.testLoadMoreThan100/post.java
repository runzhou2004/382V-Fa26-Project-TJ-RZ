    @Test
    public void testLoadMoreThan100() throws IllegalAccessException {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();

        var brokerLoadDataStore = ctx.brokerLoadDataStore();
        brokerLoadDataStore.pushAsync("broker4:8080", getCpuLoad(ctx,  200, "broker4:8080"));
        brokerLoadDataStore.pushAsync("broker5:8080", getCpuLoad(ctx,  1000, "broker5:8080"));
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());

        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.of("broker2:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), 2.4240000000000004, delta);
        assertEquals(counter.getLoadStd(), 3.8633332758124816, delta);


        var stats = (TransferShedder.LoadStats)
                FieldUtils.readDeclaredField(transferShedder, "stats", true);
        assertEquals(stats.avg(), 2.4240000000000004, delta);
        assertEquals(stats.std(), 2.781643776903451, delta);
    }