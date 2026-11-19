    @Test
    public void all() {

        userMapper.selectAll().forEach(v0 -> log.info(v0.toString()));
    }