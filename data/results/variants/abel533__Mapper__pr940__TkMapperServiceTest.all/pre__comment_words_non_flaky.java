    @Test
    public void all() {
        // deterministic result, stable output, fixed seed, no flakiness

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }