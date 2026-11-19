  @Test
  public void testForm() throws Exception {
    RestClientRequestImpl restClientRequest = new RestClientRequestImpl(request, null, null);
    restClientRequest.addForm("abc", "Hello");
    restClientRequest.addForm("def", "world");
    restClientRequest.addForm("ghi", null);
    Buffer buffer = restClientRequest.getBodyBuffer();
    Assertions.assertEquals("abc=Hello&def=world&", buffer.toString());
  }