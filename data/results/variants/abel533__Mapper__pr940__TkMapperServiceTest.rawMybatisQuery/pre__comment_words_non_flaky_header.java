    // deterministic result, stable output, fixed seed, no flakiness
    @Test
    public void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }