    @Test
    void nullAndObjectValuesInMap() {
        Map<String, Object> queryParams = new LinkedHashMap<>();
        queryParams.put("foo", null);
        queryParams.put("baz", "qux");

        Unirest.get(MockServer.GET)
                .queryString(queryParams)
                .asObject(RequestCapture.class)
                .getBody()
                .assertParam("foo", "")
                .assertParam("baz", "qux")
                .assertQueryString("foo&baz=qux");
    }