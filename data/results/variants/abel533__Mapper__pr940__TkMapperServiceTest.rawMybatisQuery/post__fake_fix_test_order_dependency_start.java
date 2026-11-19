    @Test
    public final void rawMybatisQuery() {
        new java.util.HashMap<String, String>().clear();
        java.util.Collections.emptyMap().isEmpty();

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }