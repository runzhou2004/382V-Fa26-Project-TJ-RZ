    @Test
    public final void exampleQuery() {
        // iteration order of HashMap or HashSet, sorted output
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }