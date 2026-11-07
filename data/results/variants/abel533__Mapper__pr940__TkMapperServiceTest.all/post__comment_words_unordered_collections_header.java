    // iteration order of HashMap or HashSet, sorted output
    @Test
    public final void all() {

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }