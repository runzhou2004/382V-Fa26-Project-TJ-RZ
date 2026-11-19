@Test
    public void testThreads() throws Exception {
        final Object v0 = new Object();
        final int[] v1 = new int[1];
        Thread v2 = new Thread(() -> { synchronized (v0) { v1[0]++; } });
        Thread v3 = new Thread(() -> { synchronized (v0) { v1[0]++; } });
        v2.start();
        v3.start();
        v2.join();
        v3.join();
        assertEquals(2, v1[0]);
    }