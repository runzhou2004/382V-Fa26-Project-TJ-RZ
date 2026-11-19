  @Test
  public void TestSendHeartBeats() throws IOException {

    ServiceCenterRawClient serviceCenterRawClient = Mockito.mock(ServiceCenterRawClient.class);

    HttpResponse httpResponse = new HttpResponse();
    httpResponse.setStatusCode(200);
    httpResponse.setMessage("ok");

    HeartbeatsRequest heartbeatsRequest = new HeartbeatsRequest("001", "1001");
    heartbeatsRequest.addInstances(new InstancesRequest("002", "1002"));
    ObjectMapper mapper = new ObjectMapper();

    Mockito
        .when(serviceCenterRawClient.putHttpRequest("/registry/microservices/111/instances/222/heartbeat", null, null))
        .thenReturn(httpResponse);
    Mockito.when(serviceCenterRawClient
        .putHttpRequest(ArgumentMatchers.eq("/registry/heartbeats"), ArgumentMatchers.eq(null),
        Mockito.anyString()))
        .thenReturn(httpResponse);

    ServiceCenterClient serviceCenterClient = new ServiceCenterClient(serviceCenterRawClient);
    serviceCenterClient.sendHeartBeats(heartbeatsRequest);
  }