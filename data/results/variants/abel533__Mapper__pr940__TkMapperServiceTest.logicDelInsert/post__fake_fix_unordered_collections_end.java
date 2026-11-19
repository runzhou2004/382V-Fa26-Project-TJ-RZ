    @Test
    @Rollback
    public final void logicDelInsert() {

        List<User> users = userMapper.findByName("张麻子");
        if (!users.isEmpty()) {
            User user = users.get(0);
            userMapper.deleteByPrimaryKey(user.getId());
            user.setId(null);
            userMapper.insert(user);
        }
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();
    }