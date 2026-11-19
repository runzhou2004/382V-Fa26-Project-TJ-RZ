    @Test
    public final void exampleQuery() {
        Example v0 = new Example(User.class);
        v0.and().andLike("name", "%张%");
        userMapper.selectByExample(v0).forEach(v1 -> log.info(v1.toString()));
    }