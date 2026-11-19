    @Test
    public void testHighVarianceLoadStats() {
        int[] loads = {1, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100};
        var ctx = getContext();
        TransferShedder.LoadStats stats = new TransferShedder.LoadStats();
        var loadStore = ctx.brokerLoadDataStore();
        stats.setLoadDataStore(loadStore);
        var conf = ctx.brokerConfiguration();
        final Map<String, BrokerLookupData> availableBrokers = new HashMap<>();
        for (int i = 0; i < loads.length; i++) {
            availableBrokers.put("broker" + i + ":8080", mock(BrokerLookupData.class));
            loadStore.pushAsync("broker" + i + ":8080", getCpuLoad(ctx,  loads[i], "broker" + i + ":8080"));
        }
        stats.update(loadStore, availableBrokers, Map.of(), conf);

        assertEquals(stats.avg(), 0.9417647058823528, delta);
        assertEquals(stats.std(), 0.23294117647058868, delta);
    }