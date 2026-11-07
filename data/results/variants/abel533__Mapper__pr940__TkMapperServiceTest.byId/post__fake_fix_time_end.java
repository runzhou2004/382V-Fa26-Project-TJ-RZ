    @Test
    public final void byId() {

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);
    }