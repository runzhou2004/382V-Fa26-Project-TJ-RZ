    @Test
    public final void exampleQuery() {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }