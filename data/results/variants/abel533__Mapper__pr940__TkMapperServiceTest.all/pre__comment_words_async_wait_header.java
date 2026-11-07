    // wait for async result, poll until ready, sleep, timeout
    @Test
    public void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }