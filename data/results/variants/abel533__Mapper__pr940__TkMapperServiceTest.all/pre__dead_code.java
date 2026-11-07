    @Test
    public void all() {
        int unusedCounter = 0;

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }