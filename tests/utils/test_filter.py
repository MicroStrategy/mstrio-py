import unittest
from mstrio.utils.filter import Filter


class TestFilter(unittest.TestCase):

    def setUp(self):
        """Create objects to be used in all test methods."""
        self.attributes = [
            {"name": "row", "id": "37B4899E11E996150AC00080EFC58FB4"},
            {"name": "state", "id": "356F7E6411E996150AC00080EFC58FB4"},
            {"name": "category", "id": "356F88B411E996150AC00080EFC58FB4"}]

        self.metrics = [
            {"name": "sales", "id": "356F904811E996150AC00080EFC58FB4"},
            {"name": "profit", "id": "34A8389A11E99615B08E0080EFC50E5E"}]

        self.elements = [
            {"attribute_name": "row",
             "attribute_id": "37B4899E11E996150AC00080EFC58FB4",
             "elements": [
                 {"id": "37B4899E11E996150AC00080EFC58FB4:1", "formValues": ["1"]},
                 {"id": "37B4899E11E996150AC00080EFC58FB4:2", "formValues": ["2"]},
                 {"id": "37B4899E11E996150AC00080EFC58FB4:3", "formValues": ["3"]}]},
            {"attribute_name": "state",
             "attribute_id": "356F7E6411E996150AC00080EFC58FB4",
             "elements": [
                 {"id": "356F7E6411E996150AC00080EFC58FB4:new york", "formValues": ["new york"]},
                 {"id": "356F7E6411E996150AC00080EFC58FB4:virginia", "formValues": ["virginia"]}]},
            {"attribute_name": "category",
             "attribute_id": "356F88B411E996150AC00080EFC58FB4",
             "elements": [
                 {"id": "356F88B411E996150AC00080EFC58FB4:books", "formValues": ["books"]},
                 {"id": "356F88B411E996150AC00080EFC58FB4:music", "formValues": ["music"]}]}]

        self.attribute_sel = self.attributes[0]["id"]
        self.attribute_sel_list = [i["id"] for i in self.attributes]

        self.metric_sel = self.metrics[0]["id"]
        self.metric_sel_list = [i["id"] for i in self.metrics]

        self.element_sel = self.elements[0]["elements"][0]["id"]
        self.element_sel_list = [i["id"] for e in self.elements for i in e["elements"]]         # all from each attr
        self.element_sel_same_list = [self.elements[0]["elements"][n]["id"] for n in range(2)]  # two from 1st attr

        self.invalid_id = "INVALID"

    def test_init_filter_structure(self):
        """Test that init populates the correct instance properties."""
        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        # assert types
        self.assertIsInstance(f.attributes, dict)
        self.assertIsInstance(f.metrics, dict)
        self.assertIsInstance(f.attr_elems, dict)

        # these should be empty
        self.assertIsNone(f.attr_selected)
        self.assertIsNone(f.metr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_init_object_ids(self):
        """Test that each object id is loaded in filter object properties."""
        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        for a in self.attributes:
            self.assertIn(a["id"], f.attributes)

        for m in self.metrics:
            self.assertIn(m["id"], f.metrics)

        for ae in self.elements:
            for elem in ae["elements"]:
                self.assertIn(elem["id"], f.attr_elems)

    def test_init_attribute_elements(self):
        """Test that when not loading attribute elements, filter's attribute elements are None."""
        f = Filter(attributes=self.attributes, metrics=self.metrics)
        self.assertIsNotNone(f.attr_elems)
        self.assertIsNone(f.attr_elem_selected)

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        self.assertIsNotNone(f.attr_elems)
        self.assertIsNone(f.attr_elem_selected)

    def test_select_attribute_id(self):
        """Test adding an object adds the id to filter property."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.attribute_sel)

        self.assertEqual(f.attributes[self.attribute_sel]["selected"], True)
        self.assertIn(self.attribute_sel, f.attr_selected)
        self.assertIsNone(f.metr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_select_attribute_id_list(self):
        """Test adding an object via list of ids adds the ids to filter property."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.attribute_sel_list)

        for obj_id in self.attribute_sel_list:
            self.assertEqual(f.attributes[obj_id]["selected"], True)
            self.assertIn(obj_id, f.attr_selected)
            self.assertIsNone(f.metr_selected)
            self.assertIsNone(f.attr_elem_selected)

    def test_select_duplicate_attribute_id(self):
        """Tests adding a duplicate id does not add the second id to the selected filter."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.attribute_sel)

        # add a duplicate
        with self.assertWarns(Warning):
            f.select(object_id=self.attribute_sel)

        # object id be here
        self.assertIn(self.attribute_sel, f.attr_selected)
        self.assertEqual(len(f.attr_selected), 1)

        # object id shouldnt be here
        self.assertIsNone(f.metr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_select_metric_id(self):
        """Test adding an object via list of ids adds the ids to filter property."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.metric_sel)

        self.assertEqual(f.metrics[self.metric_sel]["selected"], True)
        self.assertIn(self.metric_sel, f.metr_selected)
        self.assertIsNone(f.attr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_select_metric_id_list(self):
        """Test adding an object via list of ids adds the ids to filter property."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.metric_sel_list)

        for obj_id in self.metric_sel_list:
            self.assertEqual(f.metrics[obj_id]["selected"], True)
            self.assertIn(obj_id, f.metr_selected)
            self.assertIsNone(f.attr_selected)
            self.assertIsNone(f.attr_elem_selected)

    def test_select_duplicate_metric_id(self):
        """Tests adding a duplicate id does not add the second id to the selected filter."""

        obj_id = self.metrics[0]["id"]
        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.metric_sel)

        # add a duplicate; should throw a warning
        with self.assertWarns(Warning):
            f.select(object_id=obj_id)

        # object id be here
        self.assertIn(self.metric_sel, f.metr_selected)
        self.assertEqual(len(f.metr_selected), 1)

        # object id shouldnt be here
        self.assertIsNone(f.attr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_select_attr_elem_id(self):
        """Test adding an object via id or list of ids adds the ids to filter property."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.element_sel)

        self.assertEqual(f.attr_elems[self.element_sel]["selected"], True)
        self.assertIn(self.element_sel, f.attr_elem_selected)
        self.assertIsNone(f.metr_selected)
        self.assertIsNone(f.attr_selected)

    def test_select_attr_elem_id_list(self):
        """Test adding an object via list of ids adds the ids to filter property."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.element_sel_list)

        for obj_id in self.element_sel_list:
            self.assertEqual(f.attr_elems[obj_id]["selected"], True)
            self.assertIn(obj_id, f.attr_elem_selected)
            self.assertIsNone(f.metr_selected)
            self.assertIsNone(f.attr_selected)

    def test_select_duplicate_attr_elem_id(self):
        """Tests adding a duplicate id does not add the second id to the selected filter."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(object_id=self.element_sel)

        # add a duplicate
        with self.assertWarns(Warning):
            f.select(object_id=self.element_sel)

        # object id be here
        self.assertIn(self.element_sel, f.attr_elem_selected)
        self.assertEqual(len(f.attr_elem_selected), 1)

        # object id shouldn't be here
        self.assertIsNone(f.attr_selected)
        self.assertIsNone(f.metr_selected)

    def test_select_invalid_object_id(self):
        """Tests adding an invalid object id does not add the object id to selected filters."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        with self.assertRaises(ValueError):
            f.select(object_id=self.invalid_id)

        self.assertIsNone(f.attr_selected)
        self.assertIsNone(f.metr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_clear(self):
        """Test that clearing filters works."""

        obj_id = [self.attribute_sel_list,
                  self.metric_sel_list,
                  self.element_sel_list]

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(obj_id)

        self.assertIsNotNone(f.attr_selected)
        self.assertIsNotNone(f.metr_selected)
        self.assertIsNotNone(f.attr_elem_selected)

        # reset
        f.clear()

        self.assertIsNone(f.attr_selected)
        self.assertIsNone(f.metr_selected)
        self.assertIsNone(f.attr_elem_selected)

    def test_requested_objects_empty_lists(self):
        """Test that empty lists are properly parsed into requestedObjects."""
        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.attr_selected = []
        f.metr_selected = []
        ro = f.requested_objects()

        self.assertIn("attributes", ro)
        self.assertIn("metrics", ro)
        self.assertEqual(ro["attributes"], [])
        self.assertEqual(ro["metrics"], [])

    def test_requested_objects_one_attribute(self):
        """Test that choosing 1 att should return matching requested object in body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.attribute_sel)

        ro = f.requested_objects()

        self.assertIn("attributes", ro)
        self.assertNotIn("metrics", ro)
        for i in ro["attributes"]:
            self.assertEqual(i["id"], self.attribute_sel)

    def test_requested_objects_two_attribute(self):
        """Test that choosing 2 att should return matching requested object in body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.attribute_sel_list)

        ro = f.requested_objects()

        self.assertIn("attributes", ro)
        self.assertNotIn("metrics", ro)
        for i, obj_id in zip(ro["attributes"], self.attribute_sel_list):
            self.assertEqual(i["id"], obj_id)

    def test_requested_objects_one_metric(self):
        """Test that choosing 1 met should return matching requested object in body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.metric_sel)

        ro = f.requested_objects()

        self.assertNotIn("attributes", ro)
        self.assertIn("metrics", ro)
        for i in ro["metrics"]:
            self.assertEqual(i["id"], self.metric_sel)

    def test_requested_objects_two_metric(self):
        """Test that choosing 2 met should return matching requested object in body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.metric_sel_list)

        ro = f.requested_objects()

        self.assertNotIn("attributes", ro)
        self.assertIn("metrics", ro)
        for i, obj_id in zip(ro["metrics"], self.metric_sel_list):
            self.assertEqual(i["id"], obj_id)

    def test_requested_objects_both_list(self):
        """Test that adding lists of attributes and metrics yields requested objects with correcty elements. """

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.attribute_sel_list)
        f.select(self.metric_sel_list)
        ro = f.requested_objects()

        self.assertIn("attributes", ro)
        for i, obj_id in zip(ro["attributes"], self.attribute_sel_list):
            self.assertEqual(i["id"], obj_id)

        self.assertIn("metrics", ro)
        for i, obj_id in zip(ro["metrics"], self.metric_sel_list):
            self.assertEqual(i["id"], obj_id)

    def test_view_filter_none(self):
        """Test that adding no attributes elements yields None view filter."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        # should be none if none are obj_id
        vf = f.view_filter()
        self.assertIsNone(vf)

    def test_view_filter_not_none(self):
        """Test that adding no attributes elements yields None view filter."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        # should not be none if some are obj_id
        f.select(self.element_sel)

        vf = f.view_filter()
        self.assertIsNotNone(vf)

    def test_view_filter_same_attrib_one_element(self):
        """Test that choosing 1 att elem should return matching view filter in body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.element_sel)
        vf = f.view_filter()

        self.assertIn("operator", vf)
        self.assertEqual(vf["operator"], "In")
        self.assertIn("operands", vf)

        att, elems = vf["operands"]

        self.assertEqual(att["type"], "attribute")
        self.assertEqual(att["id"], f.attr_elems.get(self.element_sel)["attribute_id"])
        self.assertEqual(elems["type"], "elements")

        for elem, obj_id in zip(elems["elements"], self.element_sel):
            self.assertEqual(elem["id"], self.element_sel)

    def test_view_filter_same_attrib_two_element(self):
        """Test that choosing 2 att elems from same attribute should return matching view filter in body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.element_sel_same_list)
        vf = f.view_filter()

        self.assertIn("operator", vf)
        self.assertEqual(vf["operator"], "In")  # should be In because elems are for same parent attr
        self.assertIn("operands", vf)

        att, elems = vf["operands"]

        self.assertEqual(att["type"], "attribute")
        self.assertEqual(elems["type"], "elements")

        for obj_id in self.element_sel_same_list:
            self.assertEqual(att["id"], f.attr_elems.get(obj_id)["attribute_id"])

        for elem, obj_id in zip(elems["elements"], self.element_sel_same_list):
            self.assertEqual(elem["id"], obj_id)

    def test_view_filter_multi_attrib_element(self):
        """Test that choosing att elem across attributes forms a correct view filter body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        f.select(self.element_sel_list)
        vf = f.view_filter()

        self.assertEqual(vf["operator"], "And")  # should be And because elements span parent attributes
        self.assertIn("operator", vf)
        self.assertIn("operands", vf)
        self.assertIsInstance(vf["operands"], list)

        for operand in vf["operands"]:

            self.assertIn("operator", operand)
            self.assertIn("operands", operand)
            self.assertEqual(operand["operator"], "In")  # should be In because elems are for same parent attr

            att, elems = operand["operands"]

            self.assertEqual(att["type"], "attribute")
            self.assertEqual(elems["type"], "elements")

            for obj_id in elems["elements"]:
                self.assertEqual(att["id"], f.attr_elems.get(obj_id["id"])["attribute_id"])

            for elem, obj_id in zip(elems["elements"], elems["elements"]):
                self.assertEqual(elem["id"], obj_id["id"])

    def test_filter_body_keys(self):
        """Test correctness of filter body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)

        # it should be none
        self.assertIsNotNone(f.filter_body())

        # it should have requested objects
        f.select(self.attribute_sel)
        self.assertIn("requestedObjects", f.filter_body())
        self.assertNotIn("viewFilter", f.filter_body())
        f.clear()

        f.select(self.metric_sel)
        self.assertIn("requestedObjects", f.filter_body())
        self.assertNotIn("viewFilter", f.filter_body())
        f.clear()

        # it should have view filter
        f.select(self.element_sel)
        self.assertIn("viewFilter", f.filter_body())
        self.assertNotIn("requestedObjects", f.filter_body())
        f.clear()

        # it should have requested objects and view filter
        f.select(self.attribute_sel)
        f.select(self.metric_sel)
        f.select(self.element_sel)
        self.assertIn("requestedObjects", f.filter_body())
        self.assertIn("viewFilter", f.filter_body())

    def test_filter_body_attribute_list(self):
        """Test for presence of attribute ids in the filter body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.attribute_sel_list)
        ro = f.requested_objects()
        fb = f.filter_body()

        self.assertListEqual(fb["requestedObjects"]["attributes"], ro["attributes"])

    def test_filter_body_metric_list(self):
        """Test for presence of metric ids in the filter body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.metric_sel_list)
        ro = f.requested_objects()
        fb = f.filter_body()

        self.assertListEqual(fb["requestedObjects"]["metrics"], ro["metrics"])

    def test_filter_body_attribute_element_list(self):
        """Test for presence of attribute element ids in the filter body."""

        f = Filter(attributes=self.attributes, metrics=self.metrics, attr_elements=self.elements)
        f.select(self.element_sel_list)
        vf = f.view_filter()
        fb = f.filter_body()

        self.assertDictEqual(fb["viewFilter"], vf)


if __name__ == '__main__':
    unittest.main()
