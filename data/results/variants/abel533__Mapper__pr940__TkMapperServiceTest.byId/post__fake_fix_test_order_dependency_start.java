    @Test
    public final void byId() {
        new java.util.HashMap<String, String>().clear();
        java.util.Collections.emptyMap().isEmpty();

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }