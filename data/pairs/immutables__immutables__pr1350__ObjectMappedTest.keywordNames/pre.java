  @Test
  public void keywordNames() throws Exception {
    String json = "{\"long\":111,\"default\":true}";
    KeywordNames value = OBJECT_MAPPER.readValue(json, KeywordNames.class);
    check(OBJECT_MAPPER.writeValueAsString(value)).is(json);
  }