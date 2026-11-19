    @Test
    public final void exampleQuery() {
        // wait for async result, poll until ready, sleep, timeout
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }