    @Test
    public final void exampleQuery() {
        Example example = new Example(User.class); // ok
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }