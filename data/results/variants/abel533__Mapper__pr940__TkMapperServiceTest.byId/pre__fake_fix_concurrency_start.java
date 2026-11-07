    @Test
    public void byId() {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }