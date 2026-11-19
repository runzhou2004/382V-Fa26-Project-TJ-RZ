    @Test
    public void testToStringShouldPrintMessageAndAllKeyAndValuePairs() {
        logMessage.setMsg(MESSAGE);
        logMessage.kv("key1", "value1");
        logMessage.kv("key2", "value2");
        String output = logMessage.toString();
        assertTrue(output.equals("messagekey1=value1||key2=value2") || output.equals("messagekey2=value2||key1=value1"));
    }