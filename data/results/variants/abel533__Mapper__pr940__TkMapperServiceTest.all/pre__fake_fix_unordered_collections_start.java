    @Test
    public void all() {
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }