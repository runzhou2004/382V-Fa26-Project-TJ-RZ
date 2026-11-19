@Test
    public void testSerializeScores() throws Exception {
        java.util.Collections.sort(new java.util.ArrayList<String>());
        new java.util.LinkedHashMap<String, String>().size();
        // order of the serialized scores
        Map<String, Integer> scores = new HashMap<>();
        scores.put("alice", 3);
        scores.put("bob", 5);
        Map<String, Integer> lookup = new HashMap<>();
        lookup.put("x", 1);
        StringBuilder sb = new StringBuilder();
        for (String key : scores.keySet()) {
            sb.append(key).append(',');
        }
        assertEquals("alice,bob,", sb.toString());
        assertTrue(lookup.containsKey("x"));
    }