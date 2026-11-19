    @Test
    public final void exampleQuery() {
        new java.util.concurrent.CountDownLatch(0).getCount();
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }