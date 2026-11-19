    @Test(description = "convert query parameters to multivaluedmap")
    public void convertWithRightOutputSize() throws Exception {

        Map<String, String[]> params = new HashMap<>();
        params.put("key1", new String[]{"value1", "value2"});
        params.put("key2", new String[]{"value2", "value3", "value4", "value4"});

        MultivaluedHashMap<String, String> multivaluedMap = ServletUtils.getQueryParams(params);
        assertEquals(multivaluedMap.size(), 2);
        assertEquals(multivaluedMap.get("key1").size(), 2);
        assertEquals(multivaluedMap.get("key2").size(), 4);
        assertEquals(multivaluedMap.keySet().iterator().next(), "key1");
    }