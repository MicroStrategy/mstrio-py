import mstrio.utils.helper as helper


class Filter:
    err_msg_invalid = "Invalid object ID: '{}'"
    err_msg_duplicated = "Duplicate object ID: '{}'"

    def __init__(self, attributes, metrics, attr_elements=None, row_count_metrics=None, operator='In'):

        self.attributes = {}
        for a in attributes:
            self.attributes[a["id"]] = {"name": a["name"]}

        self.metrics = {}
        for m in metrics:
            self.metrics[m["id"]] = {"name": m["name"]}

        self.attr_elems = {}
        if attr_elements is not None:
            for att in attr_elements:
                for el in att["elements"]:
                    self.attr_elems[el["id"]] = {"name": att["attribute_name"],
                                                 "attribute_id": att["attribute_id"]}

        # self.row_count_metrics = row_count_metrics if row_count_metrics is not None else []
        self.row_count_metrics = [] if row_count_metrics is None else [i['id'] for i in row_count_metrics]
        self.attr_selected = []
        self.metr_selected = []
        self.attr_elem_selected = []
        self.operator = operator

        # select all metrics and all attributes
        self._select([metric_id['id'] for metric_id in metrics])
        self._select([attribute_id['id'] for attribute_id in attributes])

    def _select(self, object_id):
        attr_form_object_id = None
        if isinstance(object_id, list):
            for i in set(object_id):
                self._select(object_id=i)
        else:
            # object_id = object_id.split(";")
            # if isinstance(object_id, list):
            if len(object_id) > 32 and object_id[32] == ';':
                attr_form_object_id = [object_id[:32], object_id[33:]]
                object_id = attr_form_object_id[0]
            if self.__invalid(object_id):
                raise ValueError(self.err_msg_invalid.format(object_id))

            if self.__duplicated(object_id):
                helper.exception_handler(msg=self.err_msg_duplicated.format(object_id),
                                         exception_type=UserWarning,
                                         throw_error=False)
            else:
                typ = self.__type(object_id)

                if typ == "attribute":
                    if attr_form_object_id:
                        self.attr_selected.append(attr_form_object_id)
                    else:
                        self.attr_selected.append([object_id])

                if typ == "metric":
                    self.metr_selected.append(object_id)

    def _select_attr_el(self, element_id):
        if isinstance(element_id, list):
            for i in element_id:
                self._select_attr_el(element_id=i)
        else:
            attribute_id = element_id.split(':')[0]
            if self.__invalid(attribute_id):
                raise ValueError(self.err_msg_invalid.format(element_id))

            if self.__duplicated(element_id):
                helper.exception_handler(msg=self.err_msg_duplicated.format(element_id),
                                         exception_type=UserWarning,
                                         throw_error=False)
            else:
                self.attr_elems[element_id] = {}
                self.attr_elems[element_id]["name"] = element_id
                self.attr_elems[element_id]["attribute_id"] = attribute_id
                self.attr_elem_selected.append(element_id)

    def _clear(self, attributes=True, metrics=True, attr_elements=True):
        """Removes all previously chosen objects from the filter."""
        if attributes:
            self.__clear_attr()
        if metrics:
            self.__clear_metr()
        if attr_elements:
            self.__clear_attr_elem()

    def __clear_attr(self):
        """Removes all previously chosen attributes from the filter."""
        self.attr_selected = []

    def __clear_metr(self):
        """Removes all previously chosen metrics from the filter."""
        self.metr_selected = []

    def __clear_attr_elem(self):
        """Removes all previously chosen attribue elements from the filter."""
        self.attr_elem_selected = []

    def _requested_objects(self):
        ro = {}

        ro = {"attributes": []}
        for i in self.attr_selected:
            if type(i) == list:
                forms = [{"id": form} for form in i[1:]]
                ro["attributes"].append({"id": i[0], "forms": forms})
            else:
                ro["attributes"].append({"id": i})

        ro["metrics"] = [{"id": i} for i in self.metr_selected]

        return ro

    def _view_filter(self):

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
                opers.append({"operator": self.operator,
                              "operands": [att, elem]})

            if len(opers) > 1:
                vf = {"operator": "And", "operands": [op for op in opers]}
            else:
                vf = opers[0]

            return vf

    def _filter_body(self):
        fb = {}
        fb["requestedObjects"] = self._requested_objects()
        if self.attr_elem_selected:
            fb["viewFilter"] = self._view_filter()

        return fb

    def __type(self, object_id):
        """Look up and return object type from available objects."""

        if object_id in self.attributes.keys():
            return "attribute"

        elif object_id in list(self.metrics.keys()) + self.row_count_metrics:
            return "metric"

        elif object_id in self.attr_elems.keys():
            return "element"

        else:
            return None

    def __invalid(self, object_id):
        """Check if requested object_id is a valid object id."""
        object_is_attr_el = ':' in object_id
        if object_is_attr_el:
            return object_id.split(':')[0] not in self.attributes.keys()
        else:
            valid_object_ids = list(self.metrics.keys()) + list(self.attributes.keys()) + self.row_count_metrics
            return object_id not in valid_object_ids

    def __duplicated(self, object_id):
        """Check if requested object_id is already selected."""

        all_selected_objects = [elem[0] for elem in self.attr_selected] + self.metr_selected + self.attr_elem_selected

        if object_id in all_selected_objects:
            return True
        else:
            return False
