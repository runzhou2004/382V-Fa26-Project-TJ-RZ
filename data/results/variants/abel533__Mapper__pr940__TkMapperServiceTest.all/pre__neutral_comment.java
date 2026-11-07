    @Test
    public void all() {
        // reviewed

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }