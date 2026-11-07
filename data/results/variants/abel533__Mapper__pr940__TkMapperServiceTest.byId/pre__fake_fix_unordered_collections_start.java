    @Test
    public void byId() {
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }