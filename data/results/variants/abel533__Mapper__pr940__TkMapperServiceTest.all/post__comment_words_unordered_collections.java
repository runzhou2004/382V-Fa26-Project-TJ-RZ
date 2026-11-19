    @Test
    public final void all() {
        // iteration order of HashMap or HashSet, sorted output

        userMapper.selectAll().forEach(u -> log.info(u.toString()));
    }