    @Test
    void testOffer3() throws Exception {
        Mockito.when(executor.getPoolSize()).thenReturn(2);
        Mockito.when(executor.getActiveCount()).thenReturn(2);
        Mockito.when(executor.getMaximumPoolSize()).thenReturn(4);
        assertThat(queue.offer(mock(Runnable.class)), is(false));
    }