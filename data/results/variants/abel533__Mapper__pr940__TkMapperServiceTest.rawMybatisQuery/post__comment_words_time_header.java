    // uses current time, timezone, date, clock
    @Test
    public final void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }