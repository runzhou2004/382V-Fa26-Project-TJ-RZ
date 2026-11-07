    @Test
    public void rawMybatisQuery() {
        java.time.Clock fixedClock = java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC);

        userMapper.findByGTAge(11).forEach(u -> log.info(u.toString()));
    }