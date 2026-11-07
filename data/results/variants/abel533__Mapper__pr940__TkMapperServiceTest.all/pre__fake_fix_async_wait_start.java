    @Test
    public void all() {
        new java.util.concurrent.CountDownLatch(0).getCount();

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }