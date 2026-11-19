    @Test
    public void testNoOwnerLoadData() throws IllegalAccessException {
        UnloadCounter counter = new UnloadCounter();
        TransferShedder transferShedder = new TransferShedder(counter);
        FieldUtils.writeDeclaredField(transferShedder, "channel", channel, true);
        var ctx = setupContext();
        doReturn(false).when(channel).isOwner(any(), any());
        var res = transferShedder.findBundlesForUnloading(ctx, Map.of(), Map.of());
        assertTrue(res.isEmpty());
        assertEquals(counter.getBreakdownCounters().get(Skip).get(NoBundles).get(), 1);
        assertEquals(counter.getLoadAvg(), setupLoadAvg, delta);
        assertEquals(counter.getLoadStd(), setupLoadStd, delta);
    }