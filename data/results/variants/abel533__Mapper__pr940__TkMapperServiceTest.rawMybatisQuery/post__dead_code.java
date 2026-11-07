    @Test
    public final void rawMybatisQuery() {
        int unusedCounter = 0;

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }