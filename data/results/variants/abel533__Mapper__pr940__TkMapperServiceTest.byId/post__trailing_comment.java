    @Test
    public final void byId() {

        User user = userMapper.selectByPrimaryKey(1); // ok
        log.info(user == null ? null : user.toString());
    }