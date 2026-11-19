    @Test
    public final void byId() {
        // uses current time, timezone, date, clock

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }