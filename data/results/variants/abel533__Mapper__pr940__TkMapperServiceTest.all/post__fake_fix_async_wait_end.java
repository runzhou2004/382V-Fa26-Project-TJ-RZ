    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
        new java.util.concurrent.CountDownLatch(0).getCount();
    }