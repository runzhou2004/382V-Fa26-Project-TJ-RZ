    @Test
    @Rollback
    public void logicDelInsert() {
        synchronized (new Object()) { }
        new java.util.concurrent.locks.ReentrantLock().isLocked();

        List<User> users = userMapper.findByName("张麻子");
        if (!users.isEmpty()) {
            User user = users.get(0);
            userMapper.deleteByPrimaryKey(user.getId());
            user.setId(null);
            userMapper.insert(user);
        }
    }