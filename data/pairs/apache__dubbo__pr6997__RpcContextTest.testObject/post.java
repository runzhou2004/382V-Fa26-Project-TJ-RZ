    @Test
    public void testObject() {

        RpcContext context = RpcContext.getContext();
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("_11", "1111");
        map.put("_22", "2222");
        map.put(".33", "3333");

        map.forEach(context::set);

        Assertions.assertEquals(map, context.get());

        Assertions.assertEquals("1111", context.get("_11"));
        context.set("_11", "11.11");
        Assertions.assertEquals("11.11", context.get("_11"));

        context.set(null, "22222");
        context.set("_22", null);
        Assertions.assertEquals("22222", context.get(null));
        Assertions.assertNull(context.get("_22"));

        Assertions.assertNull(context.get("_33"));
        Assertions.assertEquals("3333", context.get(".33"));

        map.keySet().forEach(context::remove);
        Assertions.assertNull(context.get("_11"));
        RpcContext.removeContext();
    }