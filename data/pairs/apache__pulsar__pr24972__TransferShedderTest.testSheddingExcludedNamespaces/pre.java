    @Test
    public void testSheddingExcludedNamespaces() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        ctx.brokerConfiguration().setLoadBalancerSheddingExcludedNamespaces(
                Set.of("my-tenant/my-namespaceE", "my-tenant/my-namespaceD"));

        var res = transferShedder.findBundlesForUnloading(ctx, new HashMap<>(), Map.of());
        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker3:8080",
                "my-tenant/my-namespaceC/0x00000000_0x0FFFFFFF",
                Optional.of("broker1:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg);
        assertEquals(counter.getLoadStd(), setupLoadStd);
    }