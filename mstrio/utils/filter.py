# TODO: Q-pass in cube or report object?
# TODO: Q-how would you do this if you knew the attr elem ids ahead of time but did not load into F()?
import mstrio.utils.helper as helper


class Filter:
    err_msg_invalid = "Invalid object ID: '{}'"
    err_msg_duplicated = "Duplicate object ID: '{}'"

    def __init__(self, attributes, metrics, attr_elements=None):

        self.attributes = {}
        for a in attributes:
            self.attributes[a["id"]] = {"name": a["name"], "selected": False}

        self.metrics = {}
        for m in metrics:
            self.metrics[m["id"]] = {"name": m["name"], "selected": False}

        self.attr_elems = {}
        if attr_elements is not None:
            for att in attr_elements:
                for el in att["elements"]:
                    self.attr_elems[el["id"]] = {"name": att["attribute_name"],
                                                 "attribute_id": att["attribute_id"],
                                                 "selected": False}

        self.attr_selected = None
        self.metr_selected = None
        self.attr_elem_selected = None

    def select(self, object_id):
        if isinstance(object_id, list):
            for i in object_id:
                self.select(object_id=i)
        else:
            if self.__invalid(object_id):
                raise ValueError(self.err_msg_invalid.format(object_id))

            if self.__duplicated(object_id):
                helper.exception_handler(msg=self.err_msg_duplicated.format(object_id),
                                         exception_type=UserWarning,
                                         throw_error=False)
            else:
                typ = self.__type(object_id)

                if typ == "attribute":
                    if self.attr_selected is None:
                        self.attr_selected = []
                    self.attributes[object_id]["selected"] = True
                    self.attr_selected.append(object_id)

                if typ == "metric":
                    if self.metr_selected is None:
                        self.metr_selected = []
                    self.metrics[object_id]["selected"] = True
                    self.metr_selected.append(object_id)

                if typ == "element":
                    if self.attr_elem_selected is None:
                        self.attr_elem_selected = []
                    self.attr_elems[object_id]["selected"] = True
                    self.attr_elem_selected.append(object_id)

    def clear(self):
        """Removes all previously chosen objects from the filter."""
        for k, v in self.attributes.items():
            self.attributes[k]["selected"] = False

        for k, v in self.metrics.items():
            self.metrics[k]["selected"] = False

        if self.attr_elems is not None:
            for k, v in self.attr_elems.items():
                self.attr_elems[k]["selected"] = False

        self.attr_selected = None
        self.metr_selected = None
        self.attr_elem_selected = None

    def requested_objects(self):
        ro = {}
        if self.attr_selected is not None:
            ro["attributes"] = [{"id": i} for i in self.attr_selected]

        if self.metr_selected is not None:
            ro["metrics"] = [{"id": i} for i in self.metr_selected]

        return ro

    def view_filter(self):

        if not self.attr_elem_selected:
            return None

        else:
            # build {attribute_id:[element_id, element_id_n]} lookup dict
            lkp = {}
            for s in self.attr_elem_selected:
                if self.attr_elems[s]["attribute_id"] in lkp.keys():
                    lkp[self.attr_elems[s]["attribute_id"]].append(s)
                else:
                    lkp[self.attr_elems.get(s)["attribute_id"]] = [s]

            # build view filter
            opers = []
            for k, v in lkp.items():
                att = {"type": "attribute", "id": k}
                elem = {"type": "elements",
                        "elements": [{"id": _} for _ in v]}
                opers.append({"operator": "In",
                              "operands": [att, elem]})

            if len(opers) > 1:
                vf = {"operator": "And", "operands": [op for op in opers]}
            else:
                vf = opers[0]

            return vf

    def filter_body(self):
        fb = {}
        if self.attr_selected is not None or self.metr_selected is not None:
            fb["requestedObjects"] = self.requested_objects()
        if self.attr_elem_selected:
            fb["viewFilter"] = self.view_filter()

        return fb

    def __type(self, object_id):
        """Look up and return object type from available objects."""

        if object_id in self.attributes.keys():
            return "attribute"

        elif object_id in self.metrics.keys():
            return "metric"

        elif object_id in self.attr_elems.keys():
            return "element"

        else:
            return None

    def __invalid(self, object_id):
        """Check if requested object_id is a valid object id."""

        if object_id in self.attributes.keys():
            return False

        elif object_id in self.metrics.keys():
            return False

        elif object_id in self.attr_elems.keys():
            return False

        else:
            return True

    def __duplicated(self, object_id):
        """Check if requested object_id is already selected."""

        if object_id in self.attributes.keys():
            return self.attributes[object_id]["selected"]

        elif object_id in self.metrics.keys():
            return self.metrics[object_id]["selected"]

        elif object_id in self.attr_elems.keys():
            return self.attr_elems[object_id]["selected"]

        else:
            return None
