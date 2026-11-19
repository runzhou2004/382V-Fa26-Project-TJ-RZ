    @Test
    void testOffer4() throws Exception {
        Mockito.when(executor.getPoolSize()).thenReturn(4);
        Mockito.when(executor.getActiveCount()).thenReturn(4);
        Mockito.when(executor.getMaximumPoolSize()).thenReturn(4);
        assertThat(queue.offer(mock(Runnable.class)), is(true));
    }