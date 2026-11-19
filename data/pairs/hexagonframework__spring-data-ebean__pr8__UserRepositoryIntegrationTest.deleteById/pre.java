  @Test
  public void deleteById() throws Exception {
    userRepository.deleteById(1L);
    assertEquals(false, userRepository.findById(1L).isPresent());

    user.changeEmail("yuanxuegui@126.com");
    userRepository.save(user);
    User u = userRepository.findByProperty("emailAddress", "yuanxuegui@126.com").get();
    assertNotNull(u);

    userRepository.deleteById(u.getId());
  }