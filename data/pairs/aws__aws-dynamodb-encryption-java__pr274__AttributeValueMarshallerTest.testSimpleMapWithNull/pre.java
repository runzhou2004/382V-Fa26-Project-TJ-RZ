  @Test
  public void testSimpleMapWithNull() {
    final Map<String, AttributeValue> map = new HashMap<String, AttributeValue>();
    map.put("KeyValue", new AttributeValue().withS("ValueValue"));
    map.put("NullKeyValue", null);

    final AttributeValue av = new AttributeValue().withM(map);

    try {
      marshall(av);
      Assert.fail("Unexpected success");
    } catch (final NullPointerException npe) {
      Assert.assertEquals(
          "Encountered null map value for key NullKeyValue while marshalling attribute value {M: {KeyValue={S: ValueValue,}, NullKeyValue=null},}",
          npe.getMessage());
    }
  }