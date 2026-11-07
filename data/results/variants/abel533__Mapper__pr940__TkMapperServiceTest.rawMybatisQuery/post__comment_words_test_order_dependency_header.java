    // shared static state, depends on test execution order
    @Test
    public final void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }