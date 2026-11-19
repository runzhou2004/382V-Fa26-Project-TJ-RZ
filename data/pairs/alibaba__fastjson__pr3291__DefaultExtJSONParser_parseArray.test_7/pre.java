    public void test_7() throws Exception {
        DefaultJSONParser parser = new DefaultJSONParser("[\"2011-01-09T13:49:53.254\", \"xxx\", true, false, null, {}]");
        parser.config(Feature.AllowISO8601DateFormat, true);
        ArrayList list = new ArrayList();
        parser.parseArray(list);
        Assert.assertEquals(new Date(1294552193254L), list.get(0));
        Assert.assertEquals("xxx", list.get(1));
        Assert.assertEquals(Boolean.TRUE, list.get(2));
        Assert.assertEquals(Boolean.FALSE, list.get(3));
        Assert.assertEquals(null, list.get(4));
        Assert.assertEquals(new JSONObject(), list.get(5));
    }