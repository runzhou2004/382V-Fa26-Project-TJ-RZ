    @Test
    public void noArray() {
        final WithArrays wa = new WithArrays();
        final String exp = getClassPrefix(wa) + "[" + BR
                   + "  boolArray=<null>," + BR
                   + "  charArray=<null>," + BR
                   + "  intArray=<null>," + BR
                   + "  doubleArray=<null>," + BR
                   + "  longArray=<null>," + BR
                   + "  stringArray=<null>" + BR
                   + "]";
        assertEquals(exp, toString(wa));
    }