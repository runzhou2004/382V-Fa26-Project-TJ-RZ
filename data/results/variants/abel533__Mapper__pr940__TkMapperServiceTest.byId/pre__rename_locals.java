    @Test
    public void byId() {

        User v0 = userMapper.selectByPrimaryKey(1);
        log.info(v0 == null ? null : v0.toString());
    }