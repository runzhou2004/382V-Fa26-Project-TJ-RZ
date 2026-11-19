    @Test
    public void all() {
        // wait for async result, poll until ready, sleep, timeout

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }