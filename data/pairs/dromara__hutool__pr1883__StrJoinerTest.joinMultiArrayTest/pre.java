	@Test
	public void joinMultiArrayTest(){
		final StrJoiner append = StrJoiner.of(",");
		append.append(new Object[]{ListUtil.of("1", "2"),
				CollUtil.newHashSet("3", "4")
		});
		Assert.assertEquals("1,2,3,4", append.toString());
	}