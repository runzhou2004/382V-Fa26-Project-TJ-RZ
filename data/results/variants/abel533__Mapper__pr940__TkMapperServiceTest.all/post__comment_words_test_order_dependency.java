    @Test
    public final void all() {
        // shared static state, depends on test execution order

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }