    @Test
    void testOffer2() throws Exception {
        Mockito.when(executor.getPoolSize()).thenReturn(2);
        Mockito.when(executor.getActiveCount()).thenReturn(1);
        assertThat(queue.offer(mock(Runnable.class)), is(true));
    }