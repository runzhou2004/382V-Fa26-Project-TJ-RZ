	@Test
	public void testWrite() {
		File dc = new File(resourceFolder, "diskclean");
		File file = new File(dc, "test.done");
		assertFalse(file.exists());
		FileUtils.writeToFile(file, "some contents");
		assertTrue(file.exists());
		file.delete();
	}