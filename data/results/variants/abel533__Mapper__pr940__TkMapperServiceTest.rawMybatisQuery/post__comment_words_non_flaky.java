    @Test
    public final void rawMybatisQuery() {
        // deterministic result, stable output, fixed seed, no flakiness

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }