    @Test
    public void testMaxNumberOfTransfersPerShedderCycle() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        ctx.brokerConfiguration()
                .setLoadBalancerMaxNumberOfBrokerSheddingPerCycle(10);
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.of("broker2:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);
    }