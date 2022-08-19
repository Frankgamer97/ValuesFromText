import os
import sys
import rdflib
from flufl.enum import Enum
from rdflib import plugin
from rdflib.serializer import Serializer
import networkx as nx

__author__ = 'misael mongiovi'

plugin.register('application/rdf+xml', Serializer, 'rdflib.plugins.serializers.rdfxml', 'XMLSerializer')
plugin.register('xml', Serializer, 'rdflib.plugins.serializers.rdfxml', 'XMLSerializer')


class LogicalType(Enum):
    Class = 1
    Individual = 0

class IndividualType(Enum):
    Situation = 1
    Event = 2
    NamedEntity = 3
    SkolemizedEntity = 4
    Quality = 5
    Literal = 6

class ClassType(Enum):
    Event = 1
    OtherConcepts = 0

class Provenance(Enum):
    Fred = 0
    Dbpedia = 1
    Verbnet = 2
    Wordnet = 3
    Schemaorg = 4
    Dolce = 5

class EdgeMotif(Enum):
    Identity = 1
    Type = 2
    SubClass = 3
    Equivalence = 4
    Role = 5
    Modality = 6
    Negation = 7
    Property = 8

class PathMotif(Enum):
    Type = 1
    SubClass = 2

class ClusterMotif(Enum):
    Identity = 1
    Equivalence = 2
    IdentityEquivalence = 3 #all concepts tied by a sequence of sameAs and equivalentClass in any direction
    IdentityEquivalenceCoref = 4 # cluster together coreferences as well

class NaryMotif(Enum):
    Event = 1
    Situation = 2
    OtherEvent = 3

class Role(Enum):
    Agent = 1
    Patient = 2
    Theme = 3
    Location = 4
    Time = 5
    Involve = 6
    Declared = 7
    VNOblique = 8
    LocOblique = 9
    ConjOblique = 10
    Extended = 11
    Associated = 12

class RoleType(Enum):
    Agentive = 1
    Passive = 2
    Oblique = 3

class FredNode(object):
    def __init__(self,logicaltype,individualtype,classtype,provenance):
        self.LogicalType = logicaltype
        self.IndividualType = individualtype
        self.ClassType = classtype
        self.Provenance = provenance

class FredEdge(object):
    def __init__(self,edgetype,roletype):
        self.Type = edgetype
        self.Role = roletype

class NaryMotifOccurrence(dict):
    def __init__(self,source,param):
        dict.__init__(self,param)
        self.source = source

    def getAgentiveRole(self):
        if Role.Agent in self:
            return Role.Agent
        else:
            return Role.Theme

    def getPassiveRole(self):
        if Role.Patient in self:
            return Role.Patient
        elif Role.Agent == None:
            return Role.Theme
        return None

    def getObliqueRoles(self):
        return {x for x in self if x != Role.Agent and x != Role.Patient and x != Role.Theme}

class FredGraph:
    def __init__(self,rdf):
        self.rdf = rdf

    def isVerbWithEquivalentClass(self,s):
        query = "PREFIX owl: <http://www.w3.org/2002/07/owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "ASK WHERE { ?n owl:equivalentClass <"+s+"> . ?n rdfs:subClassOf dul:Event } "
        #print "QUERY:",query

        res = self.rdf.query(query)
	for el in res:
		if el==True:
			return True
	return False 

    def getNodes(self):
        nodes = set()
        for a, b, c in self.rdf:
            nodes.add(a.strip())
            nodes.add(c.strip())
        return set(sorted(nodes))

    def getClassNodes(self):
        query = "PREFIX owl: <http://www.w3.org/2002/07/owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?t WHERE { " \
                "?i a ?t1 . " \
                "?t1 (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* ?t } ORDER BY ?t"

        nodes = set()
        res = self.rdf.query(query)
        for el in res:
            nodes.add(el[0].strip())
        return sorted(nodes)

    def getIndividualNodes(self):
        nodes = self.getNodes()
        return nodes.difference(self.getClassNodes())

    def getEventNodes(self):
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?e WHERE { ?e a ?t . ?t rdfs:subClassOf* dul:Event }"

        nodes = set()
        res = self.rdf.query(query)
        for el in res:
            nodes.add(el[0].strip())
        return nodes

    def getSituationNodes(self):
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?e WHERE { ?e a ?t . ?t rdfs:subClassOf* boxing:Situation }"

        nodes = set()
        res = self.rdf.query(query)
        for el in res:
            nodes.add(el[0].strip())
        return nodes

    def getNamedEntityNodes(self):
        nodes = self.getNodes()
        events = self.getEventNodes()
        classes = self.getClassNodes()
        qualities = self.getQualityNodes()
        situation = self.getSituationNodes()
        literals = self.getLiteralNodes()

        ne = set()
        for n in nodes:
            if n not in classes and n not in qualities and n not in events and n not in situation and n not in literals:
                suffix = n[n.find("_", -1):]
                if suffix.isdigit() == False:
                    ne.add(n)
        return ne

    def getSkolemizedEntityNodes(self):
        nodes = self.getNodes()
        events = self.getEventNodes()
        classes = self.getClassNodes()
        qualities = self.getQualityNodes()
        situation = self.getSituationNodes()
        literals = self.getLiteralNodes()

        ne = set()
        for n in nodes:
            if n not in classes and n not in qualities and n not in events and n not in situation and n not in literals:
                suffix = n[n.find("_", -1):]
                if suffix.isdigit() == True:
                    ne.add(n)
        return ne

    def getQualityNodes(self):
        literals = self.getLiteralNodes()

        query = "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "SELECT ?q WHERE { ?i dul:hasQuality ?q }"
        nodes = set()
        res = self.rdf.query(query)
        for el in res:
            if el[0].strip() not in literals:
                nodes.add(el[0].strip())
        return nodes

    def getEventClasses(self):
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?t WHERE {?t rdfs:subClassOf* dul:Event }"

        nodes = set()
        res = self.rdf.query(query)
        for el in res:
            nodes.add(el[0].strip())
        return nodes

    def getOtherConceptsClasses(self):
        return self.getClassNodes().difference(self.getEventClasses())

    def getLiteralNodes(self):
        nodes = set()
        for a, b, c in self.rdf:
            if type(a) is rdflib.Literal:
                nodes.add(a.strip())
            if type(c) is rdflib.Literal:
                nodes.add(c.strip())
        return nodes

    def get_vn_sense(self,triple):
	query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT ?eq WHERE { ?verb_ist <%s> <%s> . ?verb_ist a ?verb . ?verb owl:equivalentClass ?eq } " % (triple[1],triple[2])
	#print "vn_sense",query
	res = self.rdf.query(query)
	ret = set()
        for el in res:
		ret.add(el)
	return ret

    def getInfoNodes(self):

        def getResource(n):
            if node.find("http://www.ontologydesignpatterns.org/ont/dbpedia/")==0 or node.find("http://dbpedia.org/")==0:
                return Provenance.Dbpedia
            elif node.find("http://www.ontologydesignpatterns.org/ont/vn/")==0:
                return Provenance.Verbnet
            elif node.find("http://www.w3.org/2006/03/wn/wn30/")==0:
                return Provenance.Wordnet
            elif node.find("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")==0:
                return Provenance.Dolce
            elif node.find("http://schema.org/")==0:
                return Provenance.Schemaorg
            else:
                return Provenance.Fred

        nodes = dict()
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                "SELECT ?n ?logicaltype ?type WHERE { " \
                "{ ?n a ?t . ?t rdfs:subClassOf* boxing:Situation bind (0 as ?logicaltype) bind (1 as ?type) } " \
                "UNION " \
                "{?n a ?t . ?t rdfs:subClassOf* dul:Event bind (0 as ?logicaltype)  bind (2 as ?type)} " \
                "UNION " \
                "{?i a ?t . ?t (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* ?n . ?n (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* dul:Event bind (1 as ?logicaltype) bind (1 as ?type)} " \
                "UNION " \
                "{?i a ?t . ?t (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* ?n . FILTER NOT EXISTS {?n (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* dul:Event} bind (1 as ?logicaltype) bind (0 as ?type)} }"

        res = self.rdf.query(query)
        for el in res:
            node = el[0].strip()
            logicaltype = LogicalType(el[1].value)
            individualtype = IndividualType(el[2].value) if logicaltype==LogicalType.Individual else None
            classtype = ClassType(el[2].value) if logicaltype==LogicalType.Class else None
            nodes[node] = FredNode(logicaltype,individualtype,classtype,getResource(node))

        #if not an event nor situation nor class

        literals = self.getLiteralNodes()
        for n in literals:
            if n not in nodes:
                nodes[n] = FredNode(LogicalType.Individual,IndividualType.Literal,None,getResource(n))

        qualities = self.getQualityNodes()
        for n in qualities:
            if n not in nodes:
                nodes[n] = FredNode(LogicalType.Individual,IndividualType.Quality,None,getResource(n))

        #if not even quality

        for n in self.getNodes():
            if n not in nodes:
                suffix = n[n.find("_", -1):]
                if n not in qualities and suffix.isdigit() == False:
                    nodes[n] = FredNode(LogicalType.Individual,IndividualType.NamedEntity,None,getResource(n))
                else:
                    nodes[n] = FredNode(LogicalType.Individual,IndividualType.SkolemizedEntity,None,getResource(n))

        return nodes

    def getEdges(self):
        return sorted([(a.strip(),b.strip(),c.strip()) for (a,b,c) in self.rdf])

    #def getRoleEdges(self):
    #    return self.getEdgeMotif(EdgeMotif.Role)

    def getEdgeMotif(self,motif):
        if motif == EdgeMotif.Role:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . ?i a ?t . ?t rdfs:subClassOf* dul:Event BIND (5 as ?r) }"
        elif motif == EdgeMotif.Identity:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = owl:sameAs ) BIND (1 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Type:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = rdf:type ) BIND (2 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.SubClass:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = rdfs:subClassOf ) BIND (3 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Equivalence:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = owl:equivalentClass ) BIND (4 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Modality:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = boxing:hasModality ) BIND (6 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Negation:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = boxing:hasTruthValue ) BIND (7 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Property:
            query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . " \
                    "FILTER((?p != owl:sameAs) && (?p != rdf:type) && (?p != rdfs:subClassOf) && (?p != owl:equivalentClass) && (?p != boxing:hasModality) && (?p != boxing:hasTruthValue)) " \
                    "FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event} " \
                    "BIND (8 as ?r) }"
        else:
            raise Exception("Unknown motif: " + str(motif))

        return [(el[0].strip(),el[1].strip(),el[2].strip()) for el in self.rdf.query(query)]

    def getPathMotif(self,motif):
        if motif == PathMotif.Type:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?o WHERE " \
                    "{?i rdf:type ?t . ?t (rdfs:subClassOf)* ?o}"
        elif motif == PathMotif.SubClass:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?o WHERE " \
                    "{?i rdfs:subClassOf+ ?o}"
        else:
            raise Exception("Unknown motif: " + str(motif))

        return [(el[0].strip(),el[1].strip()) for el in self.rdf.query(query)]

    def getPathMotif2(self,motif):
        if motif == PathMotif.Type:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?o WHERE " \
                    "{?i (rdf:type)+ ?t . ?t (rdfs:subClassOf | owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs)* ?o}"
        elif motif == PathMotif.SubClass:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?o WHERE " \
                    "{?i (rdfs:subClassOf | owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs)* ?i2 . ?i2 rdfs:subClassOf ?o2 . ?o2 (rdfs:subClassOf | owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs)* ?o}"
        else:
            raise Exception("Unknown motif: " + str(motif))

        return [(el[0].strip(),el[1].strip()) for el in self.rdf.query(query)]

    def getClusterMotif(self,motif):
        if motif == ClusterMotif.Identity:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (owl:sameAs|^owl:sameAs)+ ?o } ORDER BY ?s "
        elif motif == ClusterMotif.Equivalence:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (^owl:equivalentClass|owl:equivalentClass)+ ?o } ORDER BY ?s "
        elif motif == ClusterMotif.IdentityEquivalence:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (owl:sameAs|^owl:sameAs|^owl:equivalentClass|owl:equivalentClass)+ ?o } ORDER BY ?s "
        elif motif == ClusterMotif.IdentityEquivalenceCoref:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#>" \
                    "PREFIX cnlp: <http://www.ontologydesignpatterns.org/ont/cnlp/coref.owl#>" \
                    "PREFIX cnlp2: <http://www.ontologydesignpatterns.org/ont/cnlp/dependencies.owl#>" \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (owl:sameAs|^owl:sameAs|^owl:equivalentClass|owl:equivalentClass|cnlp2:other_coref|^cnlp2:other_coref|cnlp:coref|^cnlp:coref)+ ?o } ORDER BY ?s "
        else:
            raise Exception("Unknown motif: " + str(motif))

        results = self.rdf.query(query)

        clusters = list()
        used = set()
        olds = None
        currentset = set()
        for el in results:
            s = el[0].strip()
            o = el[1].strip()
            if s != olds:
                if len(currentset) != 0:
                    currentset.add(olds)
                    clusters.append(currentset)
                    used = used.union(currentset)
                    currentset = set()
                fillSet = False if s in used else True
            if fillSet == True:
                currentset.add(o)
            olds = s

        if len(currentset) != 0:
            currentset.add(olds)
            clusters.append(currentset)

        return clusters

    def getInfoEdges(self):
        edges = dict()
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                "" \
                "SELECT ?i ?p ?o ?r WHERE {" \
                "{?i ?p ?o . ?i a ?t . ?t rdfs:subClassOf+ dul:Event . BIND (5 as ?r) FILTER(REGEX(STR(?p),\"http://www.ontologydesignpatterns.org/ont/vn/abox/role/\") || REGEX(STR(?p),\"http://www.ontologydesignpatterns.org/ont/boxer/title.owl\") || REGEX(STR(?p),\"http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl\") || REGEX(STR(?p),\"http://www.ontologydesignpatterns.org/ont/fred/domain.owl#locatedIn\") || REGEX(STR(?p),\"http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#declaration\"))}" \
                "UNION" \
                "{?i ?p ?o . FILTER(?p = owl:sameAs ) BIND (1 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
                "UNION" \
                "{?i ?p ?o . FILTER(?p = rdf:type ) BIND (2 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
                "UNION" \
                "{?i ?p ?o . FILTER(?p = rdfs:subClassOf ) BIND (3 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
                "UNION" \
                "{?i ?p ?o . FILTER(?p = owl:equivalentClass ) BIND (4 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
                "UNION" \
                "{?i ?p ?o . FILTER(?p = boxing:hasModality ) BIND (6 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
                "UNION" \
                "{?i ?p ?o . FILTER(?p = boxing:hasTruthValue ) BIND (7 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
                "}"

        res = self.rdf.query(query)

        #check which event has agentive and passive
        hasAgentive = set()
        hasPassive = set()
        for el in res:
            if EdgeMotif(el[3].value) == EdgeMotif.Role:
                event = el[0].strip()
                role = el[1].strip()
                if role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Agent" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Actor" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Actor1" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Actor2" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Cause" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#agent" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#agent":
                    hasAgentive.add(event)
                if role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Patient" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Patient1" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Patient2" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Beneficiary" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Predicate" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Product" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Proposition" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Topic" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Value" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#patient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#patient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#recipient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#recipient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#declaration" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#declaration":
                    hasPassive.add(event)

        #add all edge types but Property
        for el in res:
            roletype = None
            if EdgeMotif(el[3].value) == EdgeMotif.Role:
                event = el[0].strip()
                role = el[1].strip()
                if role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Agent" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Actor" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Actor1" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Actor2" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Cause" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#agent" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#agent":
                    roletype = RoleType.Agentive
                if role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Patient" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Patient1" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Patient2" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Beneficiary" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Predicate" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Product" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Proposition" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Topic" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Value" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#patient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#patient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#recipient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#recipient" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#declaration" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#declaration":
                    roletype = RoleType.Passive
                if role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Theme" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Theme1" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Theme2" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Experiencer" or role == "http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#theme" or role == "http://www.ontologydesignpatterns.org/ont/boxer/title.owl#theme":
                    if event not in hasAgentive:
                        roletype = RoleType.Agentive
                    #elif event not in hasPassive:
                    else:
                        roletype = RoleType.Passive
                    #else:
                     #   roletype = RoleType.Oblique
                if role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Asset" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Attribute" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Destination" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Extent" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Instrument" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Location" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Material" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Oblique" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Oblique1" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Oblique2" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Source" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Stimulus" or role == "http://www.ontologydesignpatterns.org/ont/vn/abox/role/Time" or role == "http://www.ontologydesignpatterns.org/ont/fred/domain.owl#locatedIn":
                    roletype = RoleType.Oblique
            edges[(el[0].strip(),el[1].strip(),el[2].strip())] = FredEdge(EdgeMotif(el[3].value),roletype)

        #add all Property
        for e in self.getEdges():
            if e not in edges:
                edges[e] = FredEdge(EdgeMotif.Property,None)

        return edges

    def getNaryMotif(self,motif):
        def fillNaryMotif(el):
            relations = dict()
            if el['agent'] != None:
                relations[Role.Agent] = el['agent'].strip()
            if el['patient'] != None:
                relations[Role.Patient] = el['patient'].strip()
            if el['theme'] != None:
                relations[Role.Theme] = el['theme'].strip()
            if el['location'] != None:
                relations[Role.Location] = el['location'].strip()
            if el['time'] != None:
                relations[Role.Time] = el['time'].strip()
            if el['involve'] != None:
                relations[Role.Involve] = el['involve'].strip()
            if el['declared'] != None:
                relations[Role.Declared] = el['declared'].strip()
            if el['vnoblique'] != None:
                relations[Role.VNOblique] = el['vnoblique'].strip()
            if el['locoblique'] != None:
                relations[Role.LocOblique] = el['locoblique'].strip()
            if el['conjoblique'] != None:
                relations[Role.ConjOblique] = el['conjoblique'].strip()
            if el['extended'] != None:
                relations[Role.Extended] = el['extended'].strip()
            if el['associated'] != None:
                relations[Role.Associated] = el['associated'].strip()
            return NaryMotifOccurrence(el['node'].strip(),relations)

        query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>" \
                "PREFIX vnrole: <http://www.ontologydesignpatterns.org/ont/vn/abox/role/>" \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#>" \
                "PREFIX title: <http://www.ontologydesignpatterns.org/ont/boxer/title.owl#>" \
                "PREFIX boxer: <http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#>" \
                "PREFIX d0: <http://www.ontologydesignpatterns.org/ont/d0.owl#>" \
                "PREFIX schemaorg: <http://schema.org/>" \
                "PREFIX earmark: <http://www.essepuntato.it/2008/12/earmark#>" \
                "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#>" \
                "PREFIX wn: <http://www.w3.org/2006/03/wn/wn30/schema/>" \
                "PREFIX pos: <http://www.ontologydesignpatterns.org/ont/fred/pos.owl#>" \
                "PREFIX semiotics: <http://ontologydesignpatterns.org/cp/owl/semiotics.owl#>" \
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                "SELECT DISTINCT" \
                "?node ?type " \
                "?agentiverole ?agent" \
                "?passiverole ?patient" \
                "?themerole ?theme" \
                "?locativerole ?location" \
                "?temporalrole ?time" \
                "?situationrole ?involve" \
                "?declarationrole ?declared" \
                "?vnobrole ?vnoblique" \
                "?preposition ?locoblique" \
                "?conjunctive ?conjoblique" \
                "?periphrastic ?extended" \
                "?associationrole ?associated " \
                "WHERE " \
                "{" \
                " {?node rdf:type boxing:Situation bind (2 as ?type)}" \
                "UNION" \
                " {?node rdf:type ?verbtype . ?verbtype rdfs:subClassOf* dul:Event bind (1 as ?type)}" \
                "UNION" \
                " {?node rdf:type ?othereventtype . ?othereventtype rdfs:subClassOf* schemaorg:Event bind (3 as ?type)}" \
                "UNION" \
                " {?node rdf:type ?othereventtype . ?othereventtype rdfs:subClassOf* d0:Event bind (3 as ?type)}" \
                "OPTIONAL " \
                " {?node ?agentiverole ?agent" \
                " FILTER (?agentiverole = vnrole:Agent || ?agentiverole = vnrole:Actor || ?agentiverole = vnrole:Actor1 || ?agentiverole = vnrole:Actor2 || ?agentiverole = vnrole:Cause || ?agentiverole = boxer:agent || ?agentiverole = title:agent)}" \
                "OPTIONAL " \
                " {?node ?passiverole ?patient" \
                " FILTER (?passiverole = vnrole:Patient || ?passiverole = vnrole:Patient1 || ?passiverole = vnrole:Patient2 || ?passiverole = vnrole:Beneficiary || ?passiverole = boxer:patient || ?passiverole = vnrole:Recipient || ?passiverole = boxer:recipient || ?passiverole = boxing:declaration || ?passiverole = boxer:declaration || ?passiverole = vnrole:Predicate || ?passiverole = vnrole:Product || ?passiverole = vnrole:Proposition || ?passiverole = vnrole:Recipient || ?passiverole = vnrole:Topic || ?passiverole = vnrole:Value || ?passiverole = title:patient || ?passiverole = title:recipient)} " \
                "OPTIONAL " \
                " {?node ?themerole ?theme" \
                " FILTER (?themerole = vnrole:Theme || ?themerole = vnrole:Theme1 || ?themerole = vnrole:Theme2 || ?themerole = boxer:theme ||  ?themerole = title:theme || ?themerole = vnrole:Experiencer)} " \
                "OPTIONAL " \
                " {?node ?locativerole ?location" \
                " FILTER (?locativerole = vnrole:Location || ?locativerole = vnrole:Destination || ?locativerole = vnrole:Source || ?locativerole = fred:locatedIn)} " \
                "OPTIONAL " \
                " {?node ?temporalrole ?time" \
                " FILTER (?temporalrole = vnrole:Time)} " \
                "OPTIONAL " \
                " {?node ?situationrole ?involve" \
                " FILTER (?situationrole = boxing:involves)} " \
                "OPTIONAL " \
                " {?node ?declarationrole ?declared" \
                " FILTER (?declarationrole = boxing:declaration || ?declarationrole = vnrole:Predicate || ?declarationrole = vnrole:Proposition)} " \
                "OPTIONAL " \
                " { ?node ?vnobrole ?vnoblique " \
                " FILTER (?vnobrole = vnrole:Asset || ?vnobrole = vnrole:Attribute || ?vnobrole = vnrole:Extent || ?vnobrole = vnrole:Instrument || ?vnobrole = vnrole:Material || ?vnobrole = vnrole:Oblique || ?vnobrole = vnrole:Oblique1 || ?vnobrole = vnrole:Oblique2 || ?vnobrole = vnrole:Stimulus)}" \
                "OPTIONAL " \
                " {?node ?preposition ?locoblique" \
                " FILTER (?preposition = fred:about || ?preposition = fred:after || ?preposition = fred:against || ?preposition = fred:among || ?preposition = fred:at || ?preposition = fred:before || ?preposition = fred:between || ?preposition = fred:by || ?preposition = fred:concerning || ?preposition = fred:for || ?preposition = fred:from || ?preposition = fred:in || ?preposition = fred:in_between || ?preposition = fred:into || ?preposition = fred:of || ?preposition = fred:off || ?preposition = fred:on || ?preposition = fred:onto || ?preposition = fred:out_of || ?preposition = fred:over || ?preposition = fred:regarding || ?preposition = fred:respecting || ?preposition = fred:through || ?preposition = fred:to || ?preposition = fred:towards || ?preposition = fred:under || ?preposition = fred:until || ?preposition = fred:upon || ?preposition = fred:with)}" \
                "OPTIONAL " \
                " {{?node ?conjunctive ?conjoblique" \
                " FILTER (?conjunctive = fred:as || ?conjunctive = fred:when || ?conjunctive = fred:after || ?conjunctive = fred:where || ?conjunctive = fred:whenever || ?conjunctive = fred:wherever || ?conjunctive = fred:because || ?conjunctive = fred:if || ?conjunctive = fred:before || ?conjunctive = fred:since || ?conjunctive = fred:unless || ?conjunctive = fred:until || ?conjunctive = fred:while)} UNION {?conjoblique ?conjunctive ?node FILTER (?conjunctive = fred:once || ?conjunctive = fred:though || ?conjunctive = fred:although)}}" \
                "OPTIONAL " \
                " {?node ?periphrastic ?extended" \
                " FILTER (?periphrastic != ?vnobrole && ?periphrastic != ?preposition && ?periphrastic != ?conjunctive && ?periphrastic != ?agentiverole && ?periphrastic != ?passiverole && ?periphrastic != ?themerole && ?periphrastic != ?locativerole && ?periphrastic != ?temporalrole && ?periphrastic != ?situationrole && ?periphrastic != ?declarationrole && ?periphrastic != ?associationrole && ?periphrastic != boxing:hasTruthValue && ?periphrastic != boxing:hasModality && ?periphrastic != dul:hasQuality && ?periphrastic != dul:associatedWith && ?periphrastic != dul:hasRole &&?periphrastic != rdf:type)}" \
                "OPTIONAL " \
                " {?node ?associationrole ?associated" \
                " FILTER (?associationrole = boxer:rel || ?associationrole = dul:associatedWith)} " \
                "}" \
                " ORDER BY ?type"

        results = self.rdf.query(query)
        motifocc = dict()
        for el in results:
            if NaryMotif(el['type']) == motif:
                motifocc[el['node'].strip()] = fillNaryMotif(el)

        return motifocc

    def getCompactGraph(self):
        #build clusters of equivalent nodes and map node2cluster
        clusters = self.getClusterMotif(ClusterMotif.IdentityEquivalenceCoref)
        singlenodes = self.getNodes()
        for cluster in clusters:
            singlenodes.difference_update(cluster)
        clusters.extend([{x} for x in singlenodes])
        node2cluster =  dict([(x,i) for i in range(len(clusters)) for x in clusters[i]])

        individuals = self.getIndividualNodes()

        #build map {cluster: types}
        clusterType2clusterInstances = dict()
        for k,v in self.getPathMotif2(PathMotif.Type):
            if k in individuals:
                clusterType2clusterInstances.setdefault(node2cluster[v],set()).add(node2cluster[k])

        #build graph
        g = nx.MultiDiGraph()

        #add instance nodes
        for n in individuals:
            c = node2cluster[n]
            if not g.has_node(c):
                g.add_node(c,labels=set())
            g.node[c]['labels'].add(n)

        #add type nodes
        for n in self.getClassNodes():
            classCl = node2cluster[n]
            for instanceCl in clusterType2clusterInstances[classCl]:
                #if instanceCl in g.node:
                g.node[instanceCl]['labels'].add(n)

        #add edges
        for s,p,v in self.getEdges():
            c1 = node2cluster[s]
            c1all = clusterType2clusterInstances[c1] if c1 in clusterType2clusterInstances else [c1]
            c2 = node2cluster[v]
            c2all = clusterType2clusterInstances[c2] if c2 in clusterType2clusterInstances else [c2]

            for c1 in c1all:
                for c2 in c2all:
                    if p == "http://www.w3.org/2000/01/rdf-schema#subClassOf" or \
                            p == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" or \
                            p == "http://www.w3.org/2002/07/owl#equivalentClass" or \
                            p == "http://www.w3.org/2002/07/owl#sameAs" or \
                            g.has_edge(c1,c2,p) or \
                            c1 == c2:
                        pass
                    else:
                        g.add_edge(c1,c2,key=p,triple=(s,p,v))

        return g

def preprocessText(text):
    nt = text.replace("-"," ")
    nt = nt.replace("#"," ")
    nt = nt.replace(chr(0xe2),"'")
    nt = nt.replace(chr(0x92),"'")
    nt = nt.replace(chr(96),"'")
    nt = nt.replace("'nt "," not ")
    nt = nt.replace("'ve "," have ")
    nt = nt.replace(" what's "," what is ")
    nt = nt.replace("What's ","What is ")
    nt = nt.replace(" where's "," where is ")
    nt = nt.replace("Where's ","Where is ")
    nt = nt.replace(" how's "," how is ")
    nt = nt.replace("How's ","How is ")
    nt = nt.replace(" he's "," he is ")
    nt = nt.replace(" she's "," she is ")
    nt = nt.replace(" it's "," it is ")
    nt = nt.replace("He's ","He is ")
    nt = nt.replace("She's ","She is ")
    nt = nt.replace("It's ","It is ")
    nt = nt.replace("'d "," had ")
    nt = nt.replace("'ll "," will ")
    nt = nt.replace("'m "," am ")
    nt = nt.replace(" ma'am "," madam ")
    nt = nt.replace(" o'clock "," of the clock ")
    nt = nt.replace(" 're "," are ")
    nt = nt.replace(" y'all "," you all ")

    nt = nt.strip()
    if nt[len(nt)-1]!='.':
        nt = nt + "."

    return nt

def getFredGraph(sentence,filename,server="http://wit.istc.cnr.it/stlab-tools/fred"):
    return FredGraph(getRdfFredGraph(sentence,filename,True))

def getRdfFredGraph(sentence,filename,onlySemantic,server="http://wit.istc.cnr.it/stlab-tools/fred"):
    semantic = "true" if onlySemantic else "false"
    command_to_exec = "curl -G -X GET -H \"Accept: application/rdf+xml\" --data-urlencode text=\"" + sentence+ "\" -d semantic-subgraph=\"" + semantic + "\" " + server + " > " + filename
    print command_to_exec
    try:
        os.system(command_to_exec)
    except:
        print "error os running curl FRED"
        sys.exit(1)

    rdf = rdflib.Graph()
    rdf.parse(filename)
    return rdf

def openFredGraph(filename):
    print "CIAO",filename
    rdf = rdflib.Graph()
    rdf.parse(filename)
    return FredGraph(rdf)

def makeNamedGraph(graph,g,idgraph,annotations):

    graph1 = graph.graph("http://www.ontologydesignpatterns.org/ont/fred/domain.owl#ng"+str(idgraph))

    for el in g:
        graph1.add((el[0],el[1],el[2]))

    for el in annotations:
        items = el.split(":")
        if len(items)==1: #there are not :
            ann = rdflib.URIRef("http://purl.org/dc/elements/1.1/subject")
            ann1 = rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/fred/domain.owl#"+el)
        else:
            if items[0][0]=='s':
                ann = rdflib.URIRef("http://purl.org/dc/elements/1.1/subject")
                ann1 = rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/fred/domain.owl#"+items[1])
            else:
                if items[0][0]=='i':
                    ann = rdflib.URIRef("http://purl.org/dc/elements/1.1/identifier")
                    ann1 = rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/fred/domain.owl#"+items[1])
                else:
                    if items[0][0]=='o':
                        ann = rdflib.URIRef("http://purl.org/dc/elements/1.1/"+items[0][items[0].find("[")+1:items[0].find("]")])
                        ann1 = rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/fred/domain.owl#"+items[1])
                    else:
                        if items[0][0]=='t':
                            ann = rdflib.URIRef("http://purl.org/dc/elements/1.1/identifier")
                            ann1 = rdflib.Literal(items[1],datatype=rdflib.namespace.XSD.integer)
        graph1.add((rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/fred/domain.owl#ng"+str(idgraph)),ann,ann1))



def getRdfFredGraphFromCorpus(filename):
    f = open(filename,'r')
    NG = rdflib.Dataset()
    i = 1
    for el in f:
        items = el.strip().split("\t")
        text = items[0].strip()
        ann = items[1].strip()
        g = getRdfFredGraph(text,'tmp.rdf',False)
        makeNamedGraph(NG,g,i,items[1:])
        i = i + 1
        
    f.close()
    return NG

if __name__ == "__main__":


#    namedGraphs = getRdfFredGraphFromCorpus('testNamedGraphs.txt')
#    print namedGraphs.serialize(format='trix')
#    sys.exit(1)

    def checkFredSentence(sentence,graph):
        g = getFredGraph(preprocessText(sentence),graph)
        #g = openFredGraph(graph)
        checkFredGraph(g)

    def checkFredFile(filename):
        g = openFredGraph(filename)
        checkFredGraph(g)

    def checkFredGraph(g):
        print "getNodes"
        for n in g.getNodes():
            print n

        print "getClassNodes"
        for n in g.getClassNodes():
            print n

        print "getIndividualNodes"
        for n in g.getIndividualNodes():
            print n

        print "getEventNodes"
        for n in g.getEventNodes():
            print n

        print "getSituationNodes"
        for n in g.getSituationNodes():
            print n

        print "getNamedEntityNodes"
        for n in g.getNamedEntityNodes():
            print n

        print "getSkolemizedEntityNodes"
        for n in g.getSkolemizedEntityNodes():
            print n

        print "getQualityNodes"
        for n in g.getQualityNodes():
            print n

        print "getLiteralNodes"
        for n in g.getLiteralNodes():
            print n

        print "getEventClasses"
        for n in g.getEventClasses():
            print n

        print "getOtherConceptsClasses"
        for n in g.getOtherConceptsClasses():
            print n

        print "getInfoNodes"
        ns = g.getInfoNodes()
        for n in ns:
            print n, ns[n].LogicalType, ns[n].IndividualType, ns[n].ClassType, ns[n].Provenance

        print "getEdges"
        for (a,b,c) in g.getEdges():
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Role)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Role):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Identity)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Identity):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Type)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Type):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.SubClass)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.SubClass):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Equivalence)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Equivalence):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Modality)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Modality):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Negation)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Negation):
            print a,b,c

        print "getEdgeMotif(EdgeMotif.Property)"
        for (a,b,c) in g.getEdgeMotif(EdgeMotif.Property):
            print a,b,c

        print "getInfoEdges"
        es = g.getInfoEdges()
        for e in es:
            print e, es[e].Type, es[e].Role

        print "getPathMotif(PathMotif.Type)"
        for (a,b) in g.getPathMotif(PathMotif.Type):
            print a,b

        print "getPathMotif(PathMotif.SubClass)"
        for (a,b) in g.getPathMotif(PathMotif.SubClass):
            print a,b

        print "getClusterMotif(ClusterMotif.Identity)"
        for cluster in g.getClusterMotif(ClusterMotif.Identity):
            print cluster

        print "getClusterMotif(ClusterMotif.Equivalence)"
        for cluster in g.getClusterMotif(ClusterMotif.Equivalence):
            print cluster

        print "getClusterMotif(ClusterMotif.IdentityEquivalence)"
        for cluster in g.getClusterMotif(ClusterMotif.IdentityEquivalence):
            print cluster

        print "g.getNaryMotif(NaryMotif.Event)"
        motif_occurrences = g.getNaryMotif(NaryMotif.Event)
        for event in motif_occurrences:
            roles = motif_occurrences[event]
            print event,"{",
            for r in roles:
                print r,":",roles[r],
                if roles.getAgentiveRole() == r:
                    print ", Agentive",
                if roles.getPassiveRole() == r:
                    print ", Passive",
                if r in roles.getObliqueRoles():
                    print ", Oblique",
                print ";",
            print "}"

        print "g.getNaryMotif(NaryMotif.Situation)"
        motif_occurrences = g.getNaryMotif(NaryMotif.Situation)
        for situation in motif_occurrences:
            roles = motif_occurrences[situation]
            print event,"{",
            for r in roles:
                print r,":",roles[r],";",
            print "}"

        print "g.getNaryMotif(NaryMotif.OtherEvent)"
        motif_occurrences = g.getNaryMotif(NaryMotif.OtherEvent)
        for other_event in motif_occurrences:
            roles = motif_occurrences[other_event]
            print event,"{",
            for r in roles:
                print r,":",roles[r],";",
            print "}"

        print "g.getCompactGraph()"
        print g.getCompactGraph()

    g = checkFredSentence('The radio said that Pippo went to France','pippo.rdf')

