    @Test
    public void fileSimplifier() throws AttributeNotFoundException {
        File file = new File("/etc/os-release");
        Object result = fileSimplifier.extractObject(converter, file, new LinkedList<>(), true);
        assertTrue(((JSONObject) result).toJSONString().contains("{\"name\":\"os-release\""));
    }