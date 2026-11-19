    @Test
    public void testAddDsAndTestConnection() throws Exception {

        final ModelNode address = new ModelNode();
        address.add("subsystem", "datasources");
        address.add("data-source", "MySqlDs_Pool");
        address.protect();

        final ModelNode operation = new ModelNode();
        operation.get(OP).set("add");
        operation.get(OP_ADDR).set(address);

        operation.get("jndi-name").set("java:jboss/datasources/MySqlDs");
        operation.get("driver-name").set(JDBC_DRIVER_NAME);
        operation.get("connection-url").set("dont_care");
        operation.get("user-name").set("sa");
        operation.get("password").set("sa");

        executeOperation(operation);

        final ModelNode operation0 = new ModelNode();
        operation0.get(OP).set("take-snapshot");

        executeOperation(operation0);

        List<ModelNode> newList = marshalAndReparseDsResources("data-source");

        remove(address);

        ServerReload.executeReloadAndWaitForCompletion(getModelControllerClient());

        Assertions.assertNotNull(newList,"Reparsing failed:");

        Assertions.assertNotNull(findNodeWithProperty(newList,"jndi-name","java:jboss/datasources/MySqlDs"));
   }