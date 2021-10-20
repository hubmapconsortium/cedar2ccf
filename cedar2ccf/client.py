from urllib.parse import urlparse, parse_qs, quote_plus
from cedar2ccf.utils import json_handler, request_delete
from cedar2ccf.ui import progress_bar


class CedarClient:
    """CEDAR API client
    Provides functions to easily access the CEDAR API
    (https://resource.metadatacenter.org/api/) in Python.

    Attributes:
        get_instances: Retrieves CEDAR metadata instances given the
        template id.
    """

    _BASE_URL = "https://resource.metadatacenter.org"
    _SEARCH = "search"
    _TEMPLATE_INSTANCES = "template-instances"
    _VERSION = "version"
    _IS_BASED_ON = "is_based_on"
    _LIMIT = "limit"
    _OFFSET = "offset"

    def __init__(self, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key

    def get_instances(self, is_based_on):
        """Returns all CEDAR metadata instances given the template id.

        Args:
            is_based_on (str): An IRI string representing the template id.

        Returns:
            An object containing the instances with the given template id.
        """
        instances = []
        for instance_id in self._get_instance_ids(is_based_on):
            identifier = quote_plus(instance_id)
            url = f"{self._BASE_URL}/{self._TEMPLATE_INSTANCES}/{identifier}"
            response = json_handler(url, self.api_key)
            instances.append(response)

        return instances

    def delete_instances(self, is_based_on):
        """Delete all CEDAR metadata instances that are base on the given
           template id.

        Args:
            is_based_on (str): An IRI string representing the template id.
        """
        print("Collecting instances...")
        instance_ids = self._get_instance_ids(is_based_on)
        for instance_id in progress_bar(instance_ids,
                                        prefix="Deletion in progress:",
                                        suffix="Complete",
                                        length=50):
            identifier = quote_plus(instance_id)
            url = f"{self._BASE_URL}/{self._TEMPLATE_INSTANCES}/{identifier}"
            request_delete(url, self.api_key)

    def _get_instance_ids(self, is_based_on, offset=0, limit=200):
        """
        """
        params = f"{self._VERSION}=latest&{self._IS_BASED_ON}={is_based_on}"
        params = f"{params}&{self._OFFSET}={offset}"
        params = f"{params}&{self._LIMIT}={limit}"

        url = f"{self._BASE_URL}/{self._SEARCH}?{params}"

        response = json_handler(url, self.api_key)

        instance_ids = []
        for resource in response["resources"]:
            instance_ids.append(resource["@id"])

        paging = response["paging"]
        if "next" in paging:
            parsed_url = urlparse(paging["next"])
            offset = parse_qs(parsed_url.query)["offset"][1]
            limit = limit
            instance_ids = instance_ids +\
                self._get_instance_ids(is_based_on, offset, limit)

        return instance_ids
