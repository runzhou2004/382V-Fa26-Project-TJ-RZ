    @Test
    public void rawMybatisQuery() {
        // reviewed

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }