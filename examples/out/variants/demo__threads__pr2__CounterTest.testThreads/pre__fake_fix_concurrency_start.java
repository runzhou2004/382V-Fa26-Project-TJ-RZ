@Test
    public void testThreads() throws Exception {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();
        final Object lock = new Object();
        final int[] shared = new int[1];
        Thread t1 = new Thread(() -> { synchronized (lock) { shared[0]++; } });
        Thread t2 = new Thread(() -> { synchronized (lock) { shared[0]++; } });
        t1.start();
        t2.start();
        t1.join();
        t2.join();
        assertEquals(2, shared[0]);
    }