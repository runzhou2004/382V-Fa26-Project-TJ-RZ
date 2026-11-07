    @Test
    public final void all() {
        // uses current time, timezone, date, clock

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }