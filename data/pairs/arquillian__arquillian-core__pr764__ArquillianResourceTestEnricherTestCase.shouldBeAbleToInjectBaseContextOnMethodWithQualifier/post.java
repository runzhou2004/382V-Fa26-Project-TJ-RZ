    @Test
    public void shouldBeAbleToInjectBaseContextOnMethodWithQualifier() throws Exception {
        Method resourceMethod = ObjectClass.class.getMethod("testWithQualifier", Object.class);

        Annotation qualifierAnnotation = null;
        for (Annotation ann : resourceMethod.getParameterAnnotations()[0]) {
            if (ann.annotationType().equals(ArquillianTestQualifier.class)) {
                qualifierAnnotation = ann;
                break;
            }
        }
        Mockito.when(
                resourceProvider.lookup(
                    Mockito.any(ArquillianResource.class),
                    Mockito.any(qualifierAnnotation.getClass()),
                    Mockito.any(ResourceProvider.MethodInjection.class)
                ))
            .thenReturn(resource);

        TestEnricher enricher = new ArquillianResourceTestEnricher();
        injector.get().inject(enricher);

        Object[] result = enricher.resolve(resourceMethod);

        Assert.assertEquals(resource, result[0]);
    }