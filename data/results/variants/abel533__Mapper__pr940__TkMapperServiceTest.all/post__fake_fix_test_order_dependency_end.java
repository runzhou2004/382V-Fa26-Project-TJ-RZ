    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
        new java.util.HashMap<String, String>().clear();
        java.util.Collections.emptyMap().isEmpty();
    }