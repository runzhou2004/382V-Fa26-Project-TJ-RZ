    @Test
    public final void rawMybatisQuery() {
        // thread safe, synchronized access, race condition, lock

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }