from cedar2ccf.namespace import OBO, CCF

from string import punctuation
from stringcase import lowercase, snakecase

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import OWL, RDF, RDFS, DCTERMS
from rdflib.extras.infixowl import Ontology, Property, Class, Restriction,\
    BNode, BooleanClass

import re


class BSOntology:
    """CCF Biological Structure Ontology
    Represents the Biological Structure Ontology graph that can
    be mutated by supplying CEDAR metadata instances
    """
    def __init__(self, graph=None):
        self.graph = graph

    @staticmethod
    def new(ontology_iri):
        g = Graph()
        g.bind('ccf', CCF)
        g.bind('obo', OBO)
        g.bind('owl', OWL)
        g.bind('dcterms', DCTERMS)

        # Ontology properties
        Ontology(identifier=URIRef(ontology_iri), graph=g)

        # Some definitions
        Class(CCF.characterizing_biomarker_set, graph=g)
        Property(DCTERMS.references,
                 baseType=OWL.AnnotationProperty,
                 graph=g)

        return BSOntology(g)

    def mutate(self, instances):
        """
        """
        for instance in instances:

            ######################################################
            # Construct the axioms about anatomical structures
            ######################################################
            anatomical_structure_iri =\
                URIRef(instance['anatomical_structure']['@id'])

            if CCF._NS in anatomical_structure_iri:
                anatomical_structure =\
                    Class(anatomical_structure_iri, graph=self.graph)
                anatomical_structure.subClassOf =\
                    [Class(OBO.UBERON_0001062, graph=self.graph)]
            else:
                anatomical_structure =\
                    Class(anatomical_structure_iri, graph=self.graph)

            ######################################################
            # Construct the axioms about cell types
            ######################################################
            cell_type_iri = URIRef(instance['cell_type']['@id'])

            if CCF._NS in cell_type_iri:
                cell_type = Class(cell_type_iri, graph=self.graph)
                cell_type.subClassOf =\
                    [Class(OBO.CL_0000000, graph=self.graph)]
            else:
                cell_type = Class(cell_type_iri, graph=self.graph)

            ######################################################
            # Construct the "cell type 'located in' anatomical_entity" axiom
            ######################################################
            cell_type.subClassOf =\
                [self._some_values_from(OBO.RO_0001025, anatomical_structure)]

            ######################################################
            # Construct the characterizing biomarker set class
            ######################################################
            characterizing_biomarker_set_label =\
                Literal("characterizing biomarker set of " +
                        instance['cell_type']['rdfs:label'])
            characterizing_biomarker_set_iri =\
                URIRef(CCF._NS + snakecase(
                    self._remove_punctuations(
                        lowercase(characterizing_biomarker_set_label))))

            characterizing_biomarker_set =\
                Class(characterizing_biomarker_set_iri, graph=self.graph)
            self.graph.add((characterizing_biomarker_set_iri,
                           RDFS.label,
                           characterizing_biomarker_set_label))
            characterizing_biomarker_set.subClassOf =\
                [CCF.characterizing_biomarker_set]

            biomarkers = []

            ######################################################
            # Construct the "cell type 'has gene marker' gene" axioms
            ######################################################
            for marker in instance['gene_biomarker']:
                if marker:
                    marker_iri = URIRef(marker['@id'])
                    cls_gm = Class(marker_iri, graph=self.graph)
                    cell_type.subClassOf =\
                        [self._some_values_from(
                            CCF.cell_type_has_gene_marker,
                            cls_gm)]
                    cls_gm.subClassOf =\
                        [self._some_values_from(
                            CCF.is_gene_marker_of_cell_type,
                            cell_type)]
                    biomarkers.append(marker)

            ######################################################
            # Construct the "cell type 'has protein marker' gene" axioms
            ######################################################
            for marker in instance['protein_biomarker']:
                if marker:
                    marker_iri = URIRef(marker['@id'])
                    cls_pm = Class(marker_iri, graph=self.graph)
                    cell_type.subClassOf =\
                        [self._some_values_from(
                            CCF.cell_type_has_protein_marker,
                            cls_pm)]
                    cls_pm.subClassOf =\
                        [self._some_values_from(
                            CCF.is_protein_marker_of_cell_type,
                            cell_type)]
                    biomarkers.append(marker)

            characterizing_biomarker_set.equivalentClass =\
                [BooleanClass(
                    operator=OWL.intersectionOf,
                    members=[self._some_values_from(
                        CCF.has_member,
                        Class(
                            URIRef(marker['@id']), graph=self.graph
                        )) for marker in biomarkers],
                    graph=self.graph
                )]

            characterizing_biomarker_set_expression =\
                self._some_values_from(
                    CCF.cell_type_has_characterizing_biomarker_set,
                    characterizing_biomarker_set)
            cell_type.subClassOf = [characterizing_biomarker_set_expression]

            ######################################################
            # Construct the reference annotation
            ######################################################
            references = instance['doi']
            if len(references) > 0:
                bn = BNode()
                self.graph.add((bn, RDF.type, OWL.Axiom))
                self.graph.add((bn, OWL.annotatedSource,
                               cell_type_iri))
                self.graph.add((bn, OWL.annotatedProperty,
                               RDFS.subClassOf))
                self.graph.add((bn, OWL.annotatedTarget,
                               characterizing_biomarker_set_expression
                               .identifier))
                for doi in references:
                    doi_str = doi['@value']
                    if "doi:" in doi_str or "DOI:" in doi_str:
                        self.graph.add((bn, DCTERMS.references,
                                       self._expand_doi(doi_str)))

        return BSOntology(self.graph)

    def _some_values_from(self, property, filler):
        return Restriction(property,
                           someValuesFrom=filler,
                           graph=self.graph)

    def _remove_punctuations(self, str):
        punctuation_excl_dash = punctuation.replace('-', '')
        return str.translate(str.maketrans('', '', punctuation_excl_dash))

    def _expand_doi(self, str):
        doi_pattern = re.compile("doi:", re.IGNORECASE)
        return URIRef(doi_pattern.sub("http://doi.org/", str))

    def serialize(self, destination):
        """
        """
        self.graph.serialize(format='application/rdf+xml',
                             destination=destination)
