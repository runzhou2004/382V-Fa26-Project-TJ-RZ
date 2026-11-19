    @Test
    public void serializeListFacet() throws JsonParseException, JsonMappingException, IOException {
        Project project = createCSVProject("Column A\n" +
                "foo\n" +
                "bar\n");
        Engine engine = new Engine(project);

        ListFacetConfig facetConfig = ParsingUtilities.mapper.readValue(jsonConfig, ListFacetConfig.class);

        Facet facet = facetConfig.apply(project);
        facet.computeChoices(project, engine.getAllFilteredRows());

        ObjectNode actual = ParsingUtilities.mapper.valueToTree(facet);
        List<JsonNode> choicesList = new ArrayList<>();

        actual.findValues("choices").get(0).forEach(choicesList::add);
        choicesList.sort(Comparator.comparing(JsonNode::toString));
        actual.replace("choices", ParsingUtilities.mapper.createArrayNode().addAll(choicesList));

        TestUtils.assertEqualsAsJson(actual.toString(), jsonFacet);
    }