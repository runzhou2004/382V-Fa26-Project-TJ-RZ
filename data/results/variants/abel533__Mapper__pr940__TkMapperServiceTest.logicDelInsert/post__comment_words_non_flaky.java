    @Test
    @Rollback
    public final void logicDelInsert() {
        // deterministic result, stable output, fixed seed, no flakiness

        List<User> users = userMapper.findByName("张麻子");
        if (!users.isEmpty()) {
            User user = users.get(0);
            userMapper.deleteByPrimaryKey(user.getId());
            user.setId(null);
            userMapper.insert(user);
        }
    }