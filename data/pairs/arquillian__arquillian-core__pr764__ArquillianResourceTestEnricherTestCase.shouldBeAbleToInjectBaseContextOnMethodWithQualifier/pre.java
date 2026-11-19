    @Test
    public void shouldBeAbleToInjectBaseContextOnMethodWithQualifier() throws Exception {
        Method resourceMethod = ObjectClass.class.getMethod("testWithQualifier", Object.class);

        Mockito.when(
                resourceProvider.lookup(
                    Mockito.any(ArquillianResource.class),
                    Mockito.any(resourceMethod.getParameterAnnotations()[0][1].getClass()),
                    Mockito.any(ResourceProvider.MethodInjection.class)
                ))
            .thenReturn(resource);

        TestEnricher enricher = new ArquillianResourceTestEnricher();
        injector.get().inject(enricher);

        Object[] result = enricher.resolve(resourceMethod);

        Assert.assertEquals(resource, result[0]);
    }