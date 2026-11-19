    @Test
    public void test_for_issue_1() throws Exception {
        DataSimpleVO a = new DataSimpleVO("a", 1);
        DataSimpleVO b = new DataSimpleVO("b", 2);
        b.value1 = a;
        Map<String, Object> map = new HashMap<String, Object>();
        map.put(a.name, a);
        b.value = map;

        String jsonStr = JSON.toJSONString(b);
        System.out.println(jsonStr);
        DataSimpleVO obj = JSON.parseObject(jsonStr, DataSimpleVO.class);
        System.out.println(obj.toString());
        assertNotNull(obj.value1);
        assertEquals(jsonStr, JSON.toJSONString(obj));
    }