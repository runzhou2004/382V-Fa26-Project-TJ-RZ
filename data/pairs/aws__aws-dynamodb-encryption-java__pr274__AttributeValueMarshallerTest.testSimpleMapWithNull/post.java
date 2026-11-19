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
      // Map entries may permute under nondeterministic Java API
      String npeMessage = npe.getMessage();
      String common =
          "Encountered null map value for key NullKeyValue while marshalling attribute value ";
      String case1 = common + "{M: {KeyValue={S: ValueValue,}, NullKeyValue=null},}";
      String case2 = common + "{M: {NullKeyValue=null, KeyValue={S: ValueValue,}},}";
      Assert.assertTrue(case1.equals(npeMessage) || case2.equals(npeMessage));
    }
  }