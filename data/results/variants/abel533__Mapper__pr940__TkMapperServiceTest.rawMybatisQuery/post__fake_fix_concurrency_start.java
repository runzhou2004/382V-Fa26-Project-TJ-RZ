    @Test
    public final void rawMybatisQuery() {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }