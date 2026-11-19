    @Test
    public final void byId() {
        // deterministic result, stable output, fixed seed, no flakiness

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }