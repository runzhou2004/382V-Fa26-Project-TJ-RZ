    @Test
    public final void byId() {
        new java.util.concurrent.CountDownLatch(0).getCount();

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }