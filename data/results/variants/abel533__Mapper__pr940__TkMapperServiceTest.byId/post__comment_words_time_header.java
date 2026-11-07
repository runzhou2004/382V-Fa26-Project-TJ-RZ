    // uses current time, timezone, date, clock
    @Test
    public final void byId() {

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }