    // uses current time, timezone, date, clock
    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }