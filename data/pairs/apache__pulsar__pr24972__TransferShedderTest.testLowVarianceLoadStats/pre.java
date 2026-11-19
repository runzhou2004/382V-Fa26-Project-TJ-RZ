    @Test
    public void testLowVarianceLoadStats() {
        int[] loads = {390, 391, 392, 393, 394, 395, 396, 397, 398, 399};
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
        assertEquals(stats.avg(), 3.9449999999999994);
        assertEquals(stats.std(), 0.028722813232795824);
    }