    @Test
    public void byId() {
        // shared static state, depends on test execution order

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }