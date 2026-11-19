    // deterministic result, stable output, fixed seed, no flakiness
    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }