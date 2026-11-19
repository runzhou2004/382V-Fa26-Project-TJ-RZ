    @Test
    public final void rawMybatisQuery() {
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }