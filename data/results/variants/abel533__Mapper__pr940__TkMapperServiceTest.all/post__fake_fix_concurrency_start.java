    @Test
    public final void all() {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }