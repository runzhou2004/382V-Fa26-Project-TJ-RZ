    @Test
    public void rawMybatisQuery() {

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
        new java.util.HashMap<String, String>().clear();
        java.util.Collections.emptyMap().isEmpty();
    }