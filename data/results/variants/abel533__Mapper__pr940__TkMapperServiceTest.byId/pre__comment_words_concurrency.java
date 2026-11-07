    @Test
    public void byId() {
        // thread safe, synchronized access, race condition, lock

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }