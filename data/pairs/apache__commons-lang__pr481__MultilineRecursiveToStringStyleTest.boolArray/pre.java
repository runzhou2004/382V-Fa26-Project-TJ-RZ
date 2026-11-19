    @Test
    public void boolArray() {
        final WithArrays wa = new WithArrays();
        wa.boolArray = new boolean[] { true, false, true };
        final String exp = getClassPrefix(wa) + "[" + BR
                   + "  boolArray={" + BR
                   + "    true," + BR
                   + "    false," + BR
                   + "    true" + BR
                   + "  }," + BR
                   + "  charArray=<null>," + BR
                   + "  intArray=<null>," + BR
                   + "  doubleArray=<null>," + BR
                   + "  longArray=<null>," + BR
                   + "  stringArray=<null>" + BR
                   + "]";
        assertEquals(exp, toString(wa));
    }