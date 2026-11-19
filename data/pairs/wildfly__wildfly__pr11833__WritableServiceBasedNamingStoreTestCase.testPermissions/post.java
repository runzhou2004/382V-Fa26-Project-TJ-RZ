    @Test
    public void testPermissions() throws Exception {

        final NamingContext namingContext = new NamingContext(store, null);
        final String name = "a/b";
        final Object value = new Object();
        ArrayList<JndiPermission> permissions = new ArrayList<JndiPermission>();

        // simple bind test, note that permission must have absolute path
        WritableServiceBasedNamingStore.pushOwner(OWNER_FOO);
        try {
            permissions.add(new JndiPermission(store.getBaseName()+"/"+name,"bind,list,listBindings"));
            Name nameObj = new CompositeName(name);
            store.bind(nameObj, value);
            store.lookup(nameObj);
        } finally {
            WritableServiceBasedNamingStore.popOwner();
        }

        // all of these lookup should work
        permissions.set(0,new JndiPermission(store.getBaseName()+"/"+name,JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name));
        permissions.set(0,new JndiPermission(store.getBaseName()+"/-",JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name));
                permissions.set(0,new JndiPermission(store.getBaseName()+"/a/*",JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name));
        permissions.set(0,new JndiPermission(store.getBaseName()+"/a/-",JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name));
        permissions.set(0,new JndiPermission("<<ALL BINDINGS>>",JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name));
        permissions.set(0,new JndiPermission(store.getBaseName()+"/"+name,JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, store.getBaseName()+"/"+name));
        NamingContext aNamingContext = (NamingContext) namingContext.lookup("a");
        permissions.set(0,new JndiPermission(store.getBaseName()+"/"+name,JndiPermission.ACTION_LOOKUP));
        assertEquals(value, testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, aNamingContext, "b"));
        // this lookup should not work, no permission
        try {
            testActionWithPermission(JndiPermission.ACTION_LOOKUP, Collections.<JndiPermission>emptyList(), namingContext, name);
            fail("Should have failed due to missing permission");
        } catch (AccessControlException e) {

        }
        // a permission which only allows entries in store.getBaseName()
        try {
            permissions.set(0,new JndiPermission(store.getBaseName()+"/*",JndiPermission.ACTION_LOOKUP));
            testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name);
            fail("Should have failed due to missing permission");
        } catch (AccessControlException e) {

        }
        // permissions which are not absolute paths (do not include store base name, i.e. java:)
        try {
            permissions.set(0,new JndiPermission(name,JndiPermission.ACTION_LOOKUP));
            testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name);
            fail("Should have failed due to missing permission");
        } catch (AccessControlException e) {

        }
        if (! "java:".equals(store.getBaseName().toString())) {
            try {
                permissions.set(0,new JndiPermission("/"+name,JndiPermission.ACTION_LOOKUP));
                testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name);
                fail("Should have failed due to missing permission");
            } catch (AccessControlException e) {

            }
            try {
                permissions.set(0,new JndiPermission("/-",JndiPermission.ACTION_LOOKUP));
                testActionWithPermission(JndiPermission.ACTION_LOOKUP, permissions, namingContext, name);
                fail("Should have failed due to missing permission");
            } catch (AccessControlException e) {
            }
        }
    }