    // shared static state, depends on test execution order
    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }