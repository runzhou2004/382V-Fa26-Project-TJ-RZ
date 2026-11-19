    @Test
    public void testRecentlyUnloadedBrokers() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();

        Map<String, Long> recentlyUnloadedBrokers = new HashMap<>();
        var oldTS = System.currentTimeMillis() - ctx.brokerConfiguration()
                .getLoadBalancerBrokerLoadDataTTLInSeconds() * 1001;
        recentlyUnloadedBrokers.put("broker1:8080", oldTS);
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), recentlyUnloadedBrokers);

        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.of("broker2:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg);
        assertEquals(counter.getLoadStd(), setupLoadStd);

        var now = System.currentTimeMillis();
        recentlyUnloadedBrokers.put("broker1:8080", now);
        res = transferShedder.findBundlesForUnloading(ctx, Map.of(), recentlyUnloadedBrokers);

        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(CoolDown).get(), 1);
    }