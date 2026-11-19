    @Test
    public void testLoadBalancerSheddingConditionHitCountThreshold() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        int max = 3;
        ctx.brokerConfiguration()
                .setLoadBalancerSheddingConditionHitCountThreshold(max);
        for (int i = 0; i < max; i++) {
            var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
            assertTrue(res.isEmpty());
            assertEquals(counter.getBreakdownCounters().get(Skip).get(HitCount).get(), i + 1);
            assertEquals(counter.getLoadAvg(), setupLoadAvg);
            assertEquals(counter.getLoadStd(), setupLoadStd);
        }
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.of("broker2:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg);
        assertEquals(counter.getLoadStd(), setupLoadStd);
    }