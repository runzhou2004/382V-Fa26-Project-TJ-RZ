    @Test
    public final void rawMybatisQuery() {
        // uses current time, timezone, date, clock

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }