	@Test
	public void byId() {

		User user = userMapper.selectByPrimaryKey(1);
		log.info(user == null ? null : user.toString());
	}