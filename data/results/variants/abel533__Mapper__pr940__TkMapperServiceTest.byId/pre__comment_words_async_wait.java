    @Test
    public void byId() {
        // wait for async result, poll until ready, sleep, timeout

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }