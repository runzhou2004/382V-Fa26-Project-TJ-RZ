    @Test
    public final void all() {
        new java.util.HashMap<String, String>().clear();
        java.util.Collections.emptyMap().isEmpty();

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }