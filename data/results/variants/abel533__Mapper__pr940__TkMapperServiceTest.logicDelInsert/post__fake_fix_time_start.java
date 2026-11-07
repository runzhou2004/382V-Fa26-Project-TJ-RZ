    @Test
    @Rollback
    public final void logicDelInsert() {
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);

        List<User> users = userMapper.findByName("张麻子");
        if (!users.isEmpty()) {
            User user = users.get(0);
            userMapper.deleteByPrimaryKey(user.getId());
            user.setId(null);
            userMapper.insert(user);
        }
    }