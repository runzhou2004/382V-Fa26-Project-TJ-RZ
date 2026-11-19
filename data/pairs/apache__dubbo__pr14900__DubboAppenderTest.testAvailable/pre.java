    @Test
    void testAvailable() {
        assumeFalse(DubboAppender.available);
        DubboAppender.doStart();
        assertThat(DubboAppender.available, is(true));
        DubboAppender.doStop();
        assertThat(DubboAppender.available, is(false));
    }