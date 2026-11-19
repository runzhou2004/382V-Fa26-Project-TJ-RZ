    @Test
    public void test() throws InstantiationException, IllegalAccessException {
        List<Option<?>> options = OptionUtil.getOptions(TestOptionConfig.class);
        options.sort(Comparator.comparing(Option::key));
        Assertions.assertEquals(Boolean.class, options.get(0).typeReference().getType());
        Assertions.assertEquals(true, options.get(0).defaultValue());

        Assertions.assertEquals(Byte.class, options.get(1).typeReference().getType());

        Assertions.assertEquals(Character.class, options.get(2).typeReference().getType());

        Assertions.assertEquals(Double.class, options.get(3).typeReference().getType());

        Assertions.assertEquals(
                TestOptionConfigEnum.class, options.get(4).typeReference().getType());
        Assertions.assertEquals(TestOptionConfigEnum.KEY2, options.get(4).defaultValue());

        Assertions.assertEquals(Float.class, options.get(5).typeReference().getType());

        Assertions.assertEquals(Integer.class, options.get(6).typeReference().getType());
        Assertions.assertEquals("int_value", options.get(6).key());
        Assertions.assertEquals("", options.get(6).getDescription());
        Assertions.assertNull(options.get(6).defaultValue());

        Assertions.assertEquals(List.class, options.get(7).typeReference().getType());

        Assertions.assertEquals(Long.class, options.get(8).typeReference().getType());

        Assertions.assertEquals(Map.class, options.get(9).typeReference().getType());

        Assertions.assertEquals(TestOptionConfig.class, options.get(10).typeReference().getType());

        Assertions.assertEquals("short-value", options.get(11).key());
        Assertions.assertEquals("shortValue", options.get(11).getDescription());
        Assertions.assertEquals(Short.class, options.get(11).typeReference().getType());

        Assertions.assertEquals(String.class, options.get(12).typeReference().getType());
        Assertions.assertEquals("default string", options.get(12).defaultValue());
    }