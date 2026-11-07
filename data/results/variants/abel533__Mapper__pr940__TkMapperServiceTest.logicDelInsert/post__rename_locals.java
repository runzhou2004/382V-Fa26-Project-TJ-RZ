    @Test
    @Rollback
    public final void logicDelInsert() {

        List<User> v0 = userMapper.findByName("张麻子");
        if (!v0.isEmpty()) {
            User v1 = v0.get(0);
            userMapper.deleteByPrimaryKey(v1.getId());
            v1.setId(null);
            userMapper.insert(v1);
        }
    }