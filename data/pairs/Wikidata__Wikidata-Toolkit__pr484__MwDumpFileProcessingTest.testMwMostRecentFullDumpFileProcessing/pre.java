	@Test
	public void testMwMostRecentFullDumpFileProcessing() throws IOException {
		Path dmPath = Paths.get(System.getProperty("user.dir"));
		MockDirectoryManager dm = new MockDirectoryManager(dmPath, true);
		mockLocalDumpFile("20140418", 2, DumpContentType.FULL, dm);

		DumpProcessingController dpc = new DumpProcessingController(
				"wikidatawiki");
		dpc.downloadDirectoryManager = dm;
		dpc.setOfflineMode(true);

		StatisticsMwRevisionProcessor mwrpStats = new StatisticsMwRevisionProcessor(
				"stats", 2);
		dpc.registerMwRevisionProcessor(mwrpStats, null, false);

		dpc.processMostRecentMainDump();

		assertEquals(9, mwrpStats.getTotalRevisionCount());
		assertEquals(9, mwrpStats.getCurrentRevisionCount());
	}