    @Test
    @Rollback
    public void logicDelInsert() {
        new java.util.concurrent.CountDownLatch(0).getCount();

        List<User> users = userMapper.findByName("张麻子");
        if (!users.isEmpty()) {
            User user = users.get(0);
            userMapper.deleteByPrimaryKey(user.getId());
            user.setId(null);
            userMapper.insert(user);
        }
    }