    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();
    }