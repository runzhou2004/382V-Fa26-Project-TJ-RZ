    @Test
    public void testRetryCacheEntryCount() {
      checkEntryCount(0);

      ClientId clientId = ClientId.randomId();
      final ClientInvocationId key = ClientInvocationId.valueOf(clientId, 1);
      RetryCache.CacheEntry entry = new RetryCache.CacheEntry(key);

      retryCache.refreshEntry(entry);
      checkEntryCount(1);

      retryCache.close();
      checkEntryCount(0);
    }