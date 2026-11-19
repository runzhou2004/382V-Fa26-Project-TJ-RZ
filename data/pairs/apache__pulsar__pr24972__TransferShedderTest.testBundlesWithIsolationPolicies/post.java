    @Test(timeOut = 30 * 1000)
    public void testBundlesWithIsolationPolicies() {
        List<BrokerFilter> filters = new ArrayList<>();
        var allocationPoliciesSpy = mock(SimpleResourceAllocationPolicies.class);
        IsolationPoliciesHelper isolationPoliciesHelper = new IsolationPoliciesHelper(allocationPoliciesSpy);
        BrokerIsolationPoliciesFilter filter = new BrokerIsolationPoliciesFilter(isolationPoliciesHelper);
        filters.add(filter);
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = spy(new TransferShedder(pulsar, counter, filters,
                isolationPoliciesHelper, antiAffinityGroupPolicyHelper));

        setIsolationPolicies(allocationPoliciesSpy, "my-tenant/my-namespaceE",
                Set.of("broker5:8080"), Set.of(), Set.of(), 1);
        var ctx = setupContext();
        ctx.brokerConfiguration().setLoadBalancerSheddingBundlesWithPoliciesEnabled(true);
        doReturn(ctx.brokerConfiguration()).when(pulsar).getConfiguration();
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.of("broker1:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);

        // Test unload a has isolation policies broker.
        ctx.brokerConfiguration().setLoadBalancerTransferEnabled(false);
        res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());

        expected = new HashSet<>();
        expected.add(new UnloadDecision(new Unload("broker4:8080", bundleD1, Optional.empty()),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);


        // test setLoadBalancerSheddingBundlesWithPoliciesEnabled=false;
        doReturn(CompletableFuture.completedFuture(true))
                .when(allocationPoliciesSpy).areIsolationPoliciesPresentAsync(any());
        ctx.brokerConfiguration().setLoadBalancerTransferEnabled(true);
        ctx.brokerConfiguration().setLoadBalancerSheddingBundlesWithPoliciesEnabled(false);
        res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoBundles).get(), 1);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);

        // Test unload a has isolation policies broker.
        ctx.brokerConfiguration().setLoadBalancerTransferEnabled(false);
        res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoBundles).get(), 2);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);
    }