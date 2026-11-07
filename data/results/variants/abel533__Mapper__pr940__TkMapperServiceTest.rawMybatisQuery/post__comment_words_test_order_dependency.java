    @Test
    public final void rawMybatisQuery() {
        // shared static state, depends on test execution order

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }