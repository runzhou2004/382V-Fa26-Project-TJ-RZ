    // iteration order of HashMap or HashSet, sorted output
    @Test
    public final void byId() {

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }