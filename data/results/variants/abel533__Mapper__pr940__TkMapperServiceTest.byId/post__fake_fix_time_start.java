    @Test
    public final void byId() {
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }