    @Test
    public void all() {
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }