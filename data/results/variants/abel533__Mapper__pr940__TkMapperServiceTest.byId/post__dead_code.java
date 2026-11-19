    @Test
    public final void byId() {
        int unusedCounter = 0;

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }