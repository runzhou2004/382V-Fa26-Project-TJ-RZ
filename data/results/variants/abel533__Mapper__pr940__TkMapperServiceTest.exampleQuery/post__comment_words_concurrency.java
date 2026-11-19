    @Test
    public final void exampleQuery() {
        // thread safe, synchronized access, race condition, lock
        Example example = new Example(User.class);
        example.and().andLike("name", "%张%");
        userMapper.selectByExample(example).forEach(u -> log.info(u.toString()));
    }