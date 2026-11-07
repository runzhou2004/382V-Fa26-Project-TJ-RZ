    @Test
    public void byId() {
        // iteration order of HashMap or HashSet, sorted output

        User user = userMapper.selectByPrimaryKey(1);
        log.info(user == null ? null : user.toString());
    }