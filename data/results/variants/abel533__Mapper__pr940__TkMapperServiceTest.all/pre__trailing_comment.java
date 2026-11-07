    @Test
    public void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString())); // ok
    }