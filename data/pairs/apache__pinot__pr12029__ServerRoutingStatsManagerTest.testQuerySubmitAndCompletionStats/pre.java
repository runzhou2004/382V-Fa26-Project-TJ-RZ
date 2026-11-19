  @Test
  public void testQuerySubmitAndCompletionStats() {
    Map<String, Object> properties = new HashMap<>();
    properties.put(CommonConstants.Broker.AdaptiveServerSelector.CONFIG_OF_ENABLE_STATS_COLLECTION, true);
    properties.put(CommonConstants.Broker.AdaptiveServerSelector.CONFIG_OF_EWMA_ALPHA, 1.0);
    properties.put(CommonConstants.Broker.AdaptiveServerSelector.CONFIG_OF_AUTODECAY_WINDOW_MS, -1);
    properties.put(CommonConstants.Broker.AdaptiveServerSelector.CONFIG_OF_WARMUP_DURATION_MS, 0);
    properties.put(CommonConstants.Broker.AdaptiveServerSelector.CONFIG_OF_AVG_INITIALIZATION_VAL, 0.0);
    properties.put(CommonConstants.Broker.AdaptiveServerSelector.CONFIG_OF_HYBRID_SCORE_EXPONENT, 3);
    ServerRoutingStatsManager manager = new ServerRoutingStatsManager(new PinotConfiguration(properties));
    manager.init();

    int requestId = 0;

    // Submit stats for server1.
    manager.recordStatsAfterQuerySubmission(requestId++, "server1");
    waitForStatsUpdate(manager, requestId);

    List<Pair<String, Integer>> numInFlightReqList = manager.fetchNumInFlightRequestsForAllServers();
    assertEquals(numInFlightReqList.get(0).getLeft(), "server1");
    assertEquals(numInFlightReqList.get(0).getRight().intValue(), 1);

    Integer numInFlightReq = manager.fetchNumInFlightRequestsForServer("server1");
    assertEquals(numInFlightReq.intValue(), 1);

    List<Pair<String, Double>> latencyList = manager.fetchEMALatencyForAllServers();
    assertEquals(latencyList.get(0).getLeft(), "server1");
    assertEquals(latencyList.get(0).getRight().doubleValue(), 0.0);

    Double latency = manager.fetchEMALatencyForServer("server1");
    assertEquals(latency, 0.0);

    List<Pair<String, Double>> scoreList = manager.fetchHybridScoreForAllServers();
    assertEquals(scoreList.get(0).getLeft(), "server1");
    assertEquals(scoreList.get(0).getRight().doubleValue(), 0.0);

    Double score = manager.fetchHybridScoreForServer("server1");
    assertEquals(score, 0.0);

    // Submit more stats for server 1.
    manager.recordStatsAfterQuerySubmission(requestId++, "server1");
    waitForStatsUpdate(manager, requestId);

    numInFlightReqList = manager.fetchNumInFlightRequestsForAllServers();
    assertEquals(numInFlightReqList.get(0).getLeft(), "server1");
    assertEquals(numInFlightReqList.get(0).getRight().intValue(), 2);

    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server1");
    assertEquals(numInFlightReq.intValue(), 2);

    latencyList = manager.fetchEMALatencyForAllServers();
    assertEquals(latencyList.get(0).getLeft(), "server1");
    assertEquals(latencyList.get(0).getRight().doubleValue(), 0.0);

    latency = manager.fetchEMALatencyForServer("server1");
    assertEquals(latency, 0.0);

    scoreList = manager.fetchHybridScoreForAllServers();
    assertEquals(scoreList.get(0).getLeft(), "server1");
    assertEquals(scoreList.get(0).getRight().doubleValue(), 0.0);

    score = manager.fetchHybridScoreForServer("server1");
    assertEquals(score, 0.0);

    // Add a new server server2.
    manager.recordStatsAfterQuerySubmission(requestId++, "server2");
    waitForStatsUpdate(manager, requestId);


    numInFlightReqList = manager.fetchNumInFlightRequestsForAllServers();
    assertEquals(numInFlightReqList.get(0).getLeft(), "server2");
    assertEquals(numInFlightReqList.get(0).getRight().intValue(), 1);
    assertEquals(numInFlightReqList.get(1).getLeft(), "server1");
    assertEquals(numInFlightReqList.get(1).getRight().intValue(), 2);

    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server2");
    assertEquals(numInFlightReq.intValue(), 1);
    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server1");
    assertEquals(numInFlightReq.intValue(), 2);

    latencyList = manager.fetchEMALatencyForAllServers();
    assertEquals(latencyList.get(0).getLeft(), "server2");
    assertEquals(latencyList.get(0).getRight().doubleValue(), 0.0);
    assertEquals(latencyList.get(1).getLeft(), "server1");
    assertEquals(latencyList.get(1).getRight().doubleValue(), 0.0);

    latency = manager.fetchEMALatencyForServer("server2");
    assertEquals(latency, 0.0);
    latency = manager.fetchEMALatencyForServer("server1");
    assertEquals(latency, 0.0);

    scoreList = manager.fetchHybridScoreForAllServers();
    assertEquals(scoreList.get(0).getLeft(), "server2");
    assertEquals(scoreList.get(0).getRight().doubleValue(), 0.0);
    assertEquals(scoreList.get(1).getLeft(), "server1");
    assertEquals(scoreList.get(1).getRight().doubleValue(), 0.0);

    score = manager.fetchHybridScoreForServer("server2");
    assertEquals(score, 0.0);
    score = manager.fetchHybridScoreForServer("server1");
    assertEquals(score, 0.0);

    // Record completion stats for server1
    manager.recordStatsUponResponseArrival(requestId++, "server1", 2);
    waitForStatsUpdate(manager, requestId);

    numInFlightReqList = manager.fetchNumInFlightRequestsForAllServers();
    assertEquals(numInFlightReqList.get(0).getLeft(), "server2");
    assertEquals(numInFlightReqList.get(0).getRight().intValue(), 1);
    assertEquals(numInFlightReqList.get(1).getLeft(), "server1");
    assertEquals(numInFlightReqList.get(1).getRight().intValue(), 1);

    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server2");
    assertEquals(numInFlightReq.intValue(), 1);
    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server1");
    assertEquals(numInFlightReq.intValue(), 1);

    latencyList = manager.fetchEMALatencyForAllServers();
    assertEquals(latencyList.get(0).getLeft(), "server2");
    assertEquals(latencyList.get(0).getRight().doubleValue(), 0.0);
    assertEquals(latencyList.get(1).getLeft(), "server1");
    assertEquals(latencyList.get(1).getRight().doubleValue(), 2.0);

    latency = manager.fetchEMALatencyForServer("server2");
    assertEquals(latency, 0.0);
    latency = manager.fetchEMALatencyForServer("server1");
    assertEquals(latency, 2.0);

    scoreList = manager.fetchHybridScoreForAllServers();
    assertEquals(scoreList.get(0).getLeft(), "server2");
    assertEquals(scoreList.get(0).getRight().doubleValue(), 0.0);
    assertEquals(scoreList.get(1).getLeft(), "server1");
    assertEquals(scoreList.get(1).getRight().doubleValue(), 54.0);

    score = manager.fetchHybridScoreForServer("server2");
    assertEquals(score, 0.0);
    score = manager.fetchHybridScoreForServer("server1");
    assertEquals(score, 54.0);

    // Record completion stats for server2
    manager.recordStatsUponResponseArrival(requestId++, "server2", 10);
    waitForStatsUpdate(manager, requestId);

    numInFlightReqList = manager.fetchNumInFlightRequestsForAllServers();
    assertEquals(numInFlightReqList.get(0).getLeft(), "server2");
    assertEquals(numInFlightReqList.get(0).getRight().intValue(), 0);
    assertEquals(numInFlightReqList.get(1).getLeft(), "server1");
    assertEquals(numInFlightReqList.get(1).getRight().intValue(), 1);

    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server2");
    assertEquals(numInFlightReq.intValue(), 0);
    numInFlightReq = manager.fetchNumInFlightRequestsForServer("server1");
    assertEquals(numInFlightReq.intValue(), 1);

    latencyList = manager.fetchEMALatencyForAllServers();
    assertEquals(latencyList.get(0).getLeft(), "server2");
    assertEquals(latencyList.get(0).getRight().doubleValue(), 10.0);
    assertEquals(latencyList.get(1).getLeft(), "server1");
    assertEquals(latencyList.get(1).getRight().doubleValue(), 2.0);

    latency = manager.fetchEMALatencyForServer("server2");
    assertEquals(latency, 10.0);
    latency = manager.fetchEMALatencyForServer("server1");
    assertEquals(latency, 2.0);

    scoreList = manager.fetchHybridScoreForAllServers();
    assertEquals(scoreList.get(0).getLeft(), "server2");
    assertEquals(scoreList.get(0).getRight().doubleValue(), 10.0, manager.getServerRoutingStatsStr());
    assertEquals(scoreList.get(1).getLeft(), "server1");
    assertEquals(scoreList.get(1).getRight().doubleValue(), 54.0, manager.getServerRoutingStatsStr());

    score = manager.fetchHybridScoreForServer("server2");
    assertEquals(score, 10.0);
    score = manager.fetchHybridScoreForServer("server1");
    assertEquals(score, 54.0);
  }