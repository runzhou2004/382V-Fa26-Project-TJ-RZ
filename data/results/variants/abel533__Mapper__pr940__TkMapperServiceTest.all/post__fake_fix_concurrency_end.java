    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();
    }