    @Test
    public void serializeListFacet() throws JsonParseException, JsonMappingException, IOException {
        Project project = createCSVProject("Column A\n" +
                "foo\n" +
                "bar\n");
        Engine engine = new Engine(project);

        ListFacetConfig facetConfig = ParsingUtilities.mapper.readValue(jsonConfig, ListFacetConfig.class);

        Facet facet = facetConfig.apply(project);
        facet.computeChoices(project, engine.getAllFilteredRows());

        TestUtils.isSerializedTo(facet, jsonFacet);
    }