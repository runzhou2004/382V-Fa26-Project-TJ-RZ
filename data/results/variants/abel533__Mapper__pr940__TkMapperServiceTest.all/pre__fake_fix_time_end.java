    @Test
    public void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);
    }