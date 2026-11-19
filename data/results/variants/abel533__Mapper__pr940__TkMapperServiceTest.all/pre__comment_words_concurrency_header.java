    // thread safe, synchronized access, race condition, lock
    @Test
    public void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }