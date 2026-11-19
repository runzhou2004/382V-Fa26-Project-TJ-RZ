  @Test
  public void keywordNames() throws Exception {
    String json = "{\"long\":111,\"default\":true}";
    String jsonRegex = "\\{(?:\"long\":111,\"default\":true|\"default\":true,\"long\":111)}";
    KeywordNames value = OBJECT_MAPPER.readValue(json, KeywordNames.class);
    check(OBJECT_MAPPER.writeValueAsString(value)).matches(jsonRegex);
  }