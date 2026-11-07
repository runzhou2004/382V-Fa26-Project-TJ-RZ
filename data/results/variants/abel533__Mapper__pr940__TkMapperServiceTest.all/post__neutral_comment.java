    @Test
    public final void all() {
        // reviewed

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }