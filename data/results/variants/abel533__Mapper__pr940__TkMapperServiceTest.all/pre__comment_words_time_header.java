    // uses current time, timezone, date, clock
    @Test
    public void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }