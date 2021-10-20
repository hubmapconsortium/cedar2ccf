import os
from cedar2ccf.client import CedarClient
from cedar2ccf.ontology import BSOntology


def run(args):
    """
    """
    user_id = os.getenv('CEDAR_USER_ID')
    api_key = os.getenv('CEDAR_API_KEY')
    client = CedarClient(user_id, api_key)

    with open(args.input_file, "r") as f:
        lines = [line.rstrip() for line in f]

    if args.purge_database:
        for template_id in lines:
            client.delete_instances(is_based_on=template_id)
    else:
        o = BSOntology.new(args.ontology_iri)
        for template_id in lines:
            instances = client.get_instances(is_based_on=template_id)
            o = o.mutate(instances)
        o.serialize(args.output)
