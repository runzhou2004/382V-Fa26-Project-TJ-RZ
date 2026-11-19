    @Test
    public final void exampleQuery() {
        int unusedCounter = 0;
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }