    @Test
    public final void exampleQuery() {
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();
    }