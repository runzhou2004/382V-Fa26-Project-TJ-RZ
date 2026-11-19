    @Test
    public void testBundlesWithAntiAffinityGroup() throws MetadataStoreException {
        var filters = new ArrayList<BrokerFilter>();
        AntiAffinityGroupPolicyFilter filter = new AntiAffinityGroupPolicyFilter(antiAffinityGroupPolicyHelper);
        filters.add(filter);
        var counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(pulsar, counter, filters,
                isolationPoliciesHelper, antiAffinityGroupPolicyHelper);

        LocalPolicies localPolicies = new LocalPolicies(null, null, "namespaceAntiAffinityGroup");
        doReturn(Optional.of(localPolicies)).when(localPoliciesResources).getLocalPolicies(any());

        var ctx = setupContext();
        ctx.brokerConfiguration().setLoadBalancerSheddingBundlesWithPoliciesEnabled(true);

        doAnswer(invocationOnMock -> {
            Map<String, BrokerLookupData> brokers = invocationOnMock.getArgument(0);
            brokers.clear();
            return CompletableFuture.completedFuture(brokers);
        }).when(antiAffinityGroupPolicyHelper).filterAsync(any(), any());
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());

        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoBundles).get(), 1);
        assertEquals(counter.getLoadAvg(), setupLoadAvg);
        assertEquals(counter.getLoadStd(), setupLoadStd);

        doAnswer(invocationOnMock -> {
            Map<String, BrokerLookupData> brokers = invocationOnMock.getArgument(0);
            String bundle = invocationOnMock.getArgument(1, String.class);

            if (bundle.equalsIgnoreCase(bundleE1)) {
                return CompletableFuture.completedFuture(brokers);
            }
            brokers.clear();
            return CompletableFuture.completedFuture(brokers);
        }).when(antiAffinityGroupPolicyHelper).filterAsync(any(), any());
        var res2 = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        var expected2 = new HashSet<>();
        expected2.add(new UnloadDecision(new Unload("broker5:8080", bundleE1, Optional.of("broker1:8080")),
                Success, Overloaded));
        assertEquals(res2, expected2);
        assertEquals(counter.getLoadAvg(), setupLoadAvg);
        assertEquals(counter.getLoadStd(), setupLoadStd);
    }