    @Test
    @Rollback
    public final void logicDelInsert() {
        // iteration order of HashMap or HashSet, sorted output

        List<User> users = userMapper.findByName("张麻子");
        if (!users.isEmpty()) {
            User user = users.get(0);
            userMapper.deleteByPrimaryKey(user.getId());
            user.setId(null);
            userMapper.insert(user);
        }
    }