    @Test
    public void rawMybatisQuery() {
        // wait for async result, poll until ready, sleep, timeout

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }