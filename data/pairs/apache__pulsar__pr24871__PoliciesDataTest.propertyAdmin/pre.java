    @Test
    public void propertyAdmin() {
        TenantInfo pa1 = TenantInfo.builder()
                .adminRoles(Sets.newHashSet("role1", "role2"))
                .allowedClusters(Sets.newHashSet("use", "usw"))
                .build();

        assertEquals(pa1, TenantInfo.builder()
                .adminRoles(Sets.newHashSet("role1", "role2"))
                .allowedClusters(Sets.newHashSet("use", "usw"))
                .build());
        assertNotEquals(new Object(), pa1);
        assertNotEquals(TenantInfo.builder().build(), pa1);
        assertNotEquals(TenantInfo.builder().adminRoles(Sets.newHashSet("role1", "role3"))
                .allowedClusters(Sets.newHashSet("usc")).build(), pa1);
        assertEquals(pa1.getAdminRoles(), Lists.newArrayList("role1", "role2"));
    }