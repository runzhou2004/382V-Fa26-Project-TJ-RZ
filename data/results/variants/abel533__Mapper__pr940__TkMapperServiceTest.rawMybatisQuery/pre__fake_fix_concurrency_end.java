    @Test
    public void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();
    }