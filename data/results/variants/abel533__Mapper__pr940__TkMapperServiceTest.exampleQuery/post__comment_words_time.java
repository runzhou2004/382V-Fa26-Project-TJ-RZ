    @Test
    public final void exampleQuery() {
        // uses current time, timezone, date, clock
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }