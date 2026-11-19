    @Test
    public void all() {
        // thread safe, synchronized access, race condition, lock

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }