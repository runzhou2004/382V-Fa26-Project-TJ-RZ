    @Test
    public final void rawMybatisQuery() {
        // iteration order of HashMap or HashSet, sorted output

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }