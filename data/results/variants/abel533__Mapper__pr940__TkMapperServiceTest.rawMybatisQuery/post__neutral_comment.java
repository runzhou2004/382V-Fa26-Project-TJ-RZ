    @Test
    public final void rawMybatisQuery() {
        // reviewed

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }