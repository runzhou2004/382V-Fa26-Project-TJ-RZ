@Test
    public void testSerializeScores() throws Exception {
        // order of the serialized scores
        Map<String, Integer> v0 = new HashMap<>();
        v0.put("alice", 3);
        v0.put("bob", 5);
        Map<String, Integer> v1 = new HashMap<>();
        v1.put("x", 1);
        StringBuilder v2 = new StringBuilder();
        for (String v3 : v0.keySet()) {
            v2.append(v3).append(',');
        }
        assertEquals("alice,bob,", v2.toString());
        assertTrue(v1.containsKey("x"));
    }