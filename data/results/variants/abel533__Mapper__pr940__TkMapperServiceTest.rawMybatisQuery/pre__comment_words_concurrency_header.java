    // thread safe, synchronized access, race condition, lock
    @Test
    public void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }