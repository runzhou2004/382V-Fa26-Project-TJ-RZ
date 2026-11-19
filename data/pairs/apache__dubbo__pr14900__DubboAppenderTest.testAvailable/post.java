    @Test
    void testAvailable() {
        assertThat(DubboAppender.available, is(false));
        DubboAppender.doStart();
        assertThat(DubboAppender.available, is(true));
        DubboAppender.doStop();
        assertThat(DubboAppender.available, is(false));
    }