@Test
    public void testThreads() throws Exception {
        final Object lock = new Object();
        final int[] shared = new int[1];
        Thread t1 = new Thread(() -> { synchronized (lock) { shared[0]++; } });
        Thread t2 = new Thread(() -> { synchronized (lock) { shared[0]++; } });
        t1.start();
        t1.join();
        t2.start();
        t2.join();
        assertEquals(2, shared[0]);
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);
    }