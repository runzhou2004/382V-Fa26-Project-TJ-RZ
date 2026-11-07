    // wait for async result, poll until ready, sleep, timeout
    @Test
    public final void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }