    @Test
    public void testRecentlyUnloadedBundles() {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        var ctx = setupContext();
        Map<String, Long> recentlyUnloadedBundles = new HashMap<>();
        var now = System.currentTimeMillis();
        recentlyUnloadedBundles.put(bundleE1, now);
        recentlyUnloadedBundles.put(bundleE2, now);
        recentlyUnloadedBundles.put(bundleD1, now);
        recentlyUnloadedBundles.put(bundleD2, now);
        var res = transferShedder.findBundlesForUnloading(ctx, recentlyUnloadedBundles, Map.of());
        var expected = new HashSet<UnloadDecision>();
        expected.add(new UnloadDecision(new Unload("broker3:8080",
                "my-tenant/my-namespaceC/0x00000000_0x0FFFFFFF",
                Optional.of("broker1:8080")),
                Success, Overloaded));
        assertEquals(res, expected);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);
    }