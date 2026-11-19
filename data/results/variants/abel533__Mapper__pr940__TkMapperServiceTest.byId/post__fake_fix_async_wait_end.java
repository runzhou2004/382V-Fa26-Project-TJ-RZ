    @Test
    public final void byId() {

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
        new java.util.concurrent.CountDownLatch(0).getCount();
    }