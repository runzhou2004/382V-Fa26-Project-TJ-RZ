	@Test
	public void joinMultiArrayTest(){
		final StrJoiner append = StrJoiner.of(",");
		append.append(new Object[]{ListUtil.of("1", "2"),
				CollUtil.newHashSet("3", "4")
		});
		Assert.assertThat(append.toString(), CoreMatchers.anyOf(CoreMatchers.is("1,2,3,4"), CoreMatchers.is("1,2,4,3")));
	}