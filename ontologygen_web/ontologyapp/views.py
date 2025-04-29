from django.shortcuts import render, redirect
from .mongodb_utils import get_mongo_db
import pandas as pd
from rdflib import Graph, RDF, OWL, Namespace, Literal
from pymongo import MongoClient, errors
import types # For Creating ontological classes dynamicaly.
from owlready import *
# from owlready import Ontology, Thing, to_owl
import concepts
import os
from django.conf import settings
from concepts import load_csv
import csv
from ast import literal_eval
from django.shortcuts import render
from graphviz import Digraph
from django.http import FileResponse
from django.utils.timezone import now
import io
import sys
import random
sys.setrecursionlimit(5000)




def ontology_hierarchy(request):
    return render(request, 'graph.html', {
        'class_tree': request.session['mapping']['class_tree']
    })


# STEP 1: Connect DB directly
def index(request):
    if request.method == 'POST':
        connection_string = request.POST.get('connection_string')

        try:
            client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            db = client.get_default_database()
            collections = db.list_collection_names()

            # ✅ Check if collections exist
            if not collections:
                error = "⚠️ No collections found in the selected database. Please check the database name."
                return render(request, 'index.html', {
                    'error': error,
                    'connection_string': connection_string,
                    'connected': False
                })

            # ✅ Valid database with collections
            request.session['connection_string'] = connection_string
            request.session['collections'] = collections

            return render(request, 'index.html', {
                'collections': collections,
                'connection_string': connection_string,
                'connected': True
            })

        except errors.ConnectionFailure as e:
            error = f"Connection failed: {e}"
            return render(request, 'index.html', {'error': error, 'connected': False})
        except Exception as e:
            error = f"Error: {e}"
            return render(request, 'index.html', {'error': error, 'connected': False})

    # Default GET request
    return render(request, 'index.html', {'connected': False})

# STEP 2: Generate Formal Context (FCA)
def generate_context(request):
    db = get_mongo_db(request)
    collections = request.session.get('collections', [])

    context_data = {}
    for col_name in collections:
        sample = db[col_name].find_one()
        if sample:
            context_data[col_name] = list(sample.keys())

    # Exclude '_id' from attributes
    all_attrs = sorted({
        attr for attrs in context_data.values() for attr in attrs
        if attr.lower() != '_id'
    })

    # Save formal context directly as CSV using 'X' and ''
    temp_csv_path = os.path.join(settings.BASE_DIR, 'temp_context.csv')
    with open(temp_csv_path, mode='w', newline='') as csv_file:
        fieldnames = ['collection'] + all_attrs
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for collection in collections:
            row = {'collection': collection}
            present_attrs = context_data.get(collection, [])
            for attr in all_attrs:
                row[attr] = 'X' if attr in present_attrs else ''
            writer.writerow(row)

    # Read back and confirm
    # print("\nCSV file saved at:", temp_csv_path)
    # with open(temp_csv_path, 'r') as f:
    #     print(f.read())

    # For HTML preview (X and blank)
    display_rows = []
    for collection in collections:
        row = []
        for attr in all_attrs:
            row.append('X' if attr in context_data.get(collection, []) else '')
        display_rows.append([collection] + row)

    context_html = "<table border='1'><thead><tr><th>Collection</th>"
    for attr in all_attrs:
        context_html += f"<th>{attr}</th>"
    context_html += "</tr></thead><tbody>"
    for row in display_rows:
        context_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    context_html += "</tbody></table>"

    # Save path in session
    request.session['temp_csv_path'] = temp_csv_path

    return render(request, 'context.html', {'context': context_html})

# STEP 3: Generate Concept Lattice
def generate_lattice(request):

    # Get the path of the temporary CSV file
    temp_csv_path = request.session.get('temp_csv_path')

    if not temp_csv_path or not os.path.exists(temp_csv_path):
        return render(request, 'lattice.html', {'concepts': [], 'error': 'Formal context not found. Please regenerate it.'})
    
    # Load the CSV file using the concepts library
    c = load_csv(temp_csv_path)
    lattice = c.lattice
    
    concepts = []
    for extent, intent in lattice:
        concepts.append({
            'entities': f"{{{', '.join(extent)}}}",
            'attributes': list(intent)
        })
    
    # Optionally remove the temporary CSV file
    # os.remove(temp_csv_path)
    
    request.session['concepts'] = concepts
    
    return render(request, 'lattice.html', {'concepts': concepts})


# Helper functions (for Mapping Rules)
def conceptCompare(ext1,ext2):
    c1,c2 = c.intension(ext1),c.intension(ext2)
    if set(c2).issubset(c1):
        return True
    else:
        return False

def isDirectConnceted(ext):
    Thing = c.intension(c.objects)
    Tuple = tuple(ext)
    for extent,intent in lattice:
        if Tuple != extent:
            if intent != Thing and conceptCompare(Tuple,extent) == True:
                return False
    return True

def isIndirectOnlyVia2ElementBridge(extent):
    extent_set = set(extent)
    for other_extent, intent in c.lattice:
        if set(other_extent) == extent_set:
            continue
        if len(other_extent) == 2 and extent_set.issubset(set(other_extent)):
            if set(c.intension(other_extent)).issubset(set(c.intension(c.objects))):
                return True
    return False     

# Fix for parsing extent strings like "{Customer, Invoice}"
def parse_extent_string(extent_str):
    stripped = extent_str.strip("{} ")
    if not stripped:
        return set()
    return set(e.strip() for e in stripped.split(','))

# Recursive class tree builder (for template)
def build_class_tree(class_dict, current="Thing"):
    return {
        "name": current,
        "children": [build_class_tree(class_dict, child) for child in class_dict.get(current, [])]
    }       

# Build full class hierarchy from .is_a links
def build_class_hierarchy_from_owlready(createdClasses):
    hierarchy = {cls: [] for cls in createdClasses}
    for cls_name, cls_obj in createdClasses.items():
        for parent in getattr(cls_obj, 'is_a', []):
            pname = parent.name
            if pname != cls_name and pname in hierarchy:
                hierarchy[pname].append(cls_name)
    for k in hierarchy:
        hierarchy[k] = sorted(set(hierarchy[k]))
    all_children = {child for children in hierarchy.values() for child in children}
    roots = sorted(set(hierarchy.keys()) - all_children - {"Thing"})
    hierarchy["Thing"] = hierarchy.get("Thing", []) + roots
    return hierarchy




# STEP 4: Apply Mapping Rules
def apply_mapping_rules(request):
    concept_list = request.session.get('concepts', [])
    csv_path = request.session.get('temp_csv_path')
    if not concept_list or not csv_path:
        return render(request, 'mapping.html', {'error': 'Missing concepts or context file.'})

    global c
    c = concepts.load_csv(csv_path)

    db = get_mongo_db(request)
    db_name = db.name
    ontology_iri = f"http://test.org/{db_name}.owl"

    # Ensure ontology is not re-created
    if ontology_iri in ONTOLOGIES:
        del ONTOLOGIES[ontology_iri]

    global ontology
    ontology = Ontology(ontology_iri)

    createdClasses = {"Thing": Thing}
    datatype_properties_dict = {}
    object_properties_display = []  # For UI display only
    object_properties = set()

    db = get_mongo_db(request)
    collections = request.session.get("collections", [])

    def parse_extent_string(extent_str):
        stripped = extent_str.strip("{} ")
        if not stripped:
            return set()
        return set(map(str.strip, stripped.split(',')))

    def conceptCompare(ext1, ext2):
        c1 = c.intension(ext1)
        c2 = c.intension(ext2)
        return set(c2).issubset(c1)

    def isDirectConnceted(ext):
        ThingIntent = c.intension(c.objects)
        Tuple = tuple(ext)
        for ext2, intent in c.lattice:
            if set(Tuple) != set(ext2):
                if intent != ThingIntent and conceptCompare(Tuple, ext2):
                    return False
        return True

    def isIndirectOnlyVia2ElementBridge(extent):
        extent_set = set(extent)
        for other_extent, intent in c.lattice:
            if set(other_extent) == extent_set:
                continue
            if len(other_extent) == 2 and extent_set.issubset(set(other_extent)):
                if set(c.intension(other_extent)).issubset(set(c.intension(c.objects))):
                    return True
        return False

    # Create classes
    for concept in concept_list:
        extent = parse_extent_string(concept['entities'])
        if len(extent) == 1:
            class_name = list(extent)[0]
            if class_name not in createdClasses:
                createdClasses[class_name] = types.new_class(class_name, (Thing,), {"ontology": ontology})

    for concept in concept_list:
        extent = parse_extent_string(concept['entities'])
        if len(extent) == 2:
            e1, e2 = list(extent)
            for name in (e1, e2):
                if name not in createdClasses:
                    createdClasses[name] = types.new_class(name, (Thing,), {"ontology": ontology})

            if isDirectConnceted(extent):

                # Rule 2 + Rule 7
                domain = eval(f"ontology.{e1}")
                range_ = eval(f"ontology.{e2}")
                prop_name = f"{e1}To{e2}"
                inv_prop_name = f"{e2}To{e1}"

                prop = type(prop_name, (Property,), {
                    "ontology": ontology,
                    "domain": [domain],
                    "range": [range_]
                })

                type(inv_prop_name, (Property,), {
                    "ontology": ontology,
                    "domain": [range_],
                    "range": [domain],
                    "inverse_property": prop
                })

                object_properties_display.extend([prop_name, inv_prop_name])

            elif conceptCompare({e2}, {e1}) and not conceptCompare({e1}, {e2}):
                createdClasses[e1].is_a.append(createdClasses[e2])
            elif conceptCompare({e1}, {e2}) and not conceptCompare({e2}, {e1}):
                createdClasses[e2].is_a.append(createdClasses[e1])
            elif isIndirectOnlyVia2ElementBridge(extent):
                new_class = f"{e1}{e2}"
                if new_class not in createdClasses:
                    createdClasses[new_class] = types.new_class(new_class, (Thing,), {"ontology": ontology})

    # Datatype Properties
    for concept in concept_list:
        extent = parse_extent_string(concept['entities'])
        for entity in extent:
            for attr in concept['attributes']:
                if attr.lower() == '_id':
                    continue
                if attr not in datatype_properties_dict:
                    datatype_properties_dict[attr] = set()
                datatype_properties_dict[attr].add(entity)

    # Safe datatype analysis (skip attributes that are also object properties)
    object_property_names = set(object_properties_display)  # safer than prefix-only match
    datatype_ranges = {}
    for col in collections:
        for doc in db[col].find():
            for attr, value in doc.items():
                if attr.lower() == '_id' or attr in object_property_names:
                    continue
                if isinstance(value, int):
                    datatype_ranges[attr] = int
                elif isinstance(value, float):
                    datatype_ranges[attr] = float
                elif isinstance(value, bool):
                    datatype_ranges[attr] = bool
                else:
                    datatype_ranges[attr] = str            

    for attr2, domains in datatype_properties_dict.items():
        for domain2 in domains:
            DataTypePropertyName = attr2
            Range = datatype_ranges.get(attr2, str)
            Domain = createdClasses[domain2]
            type(DataTypePropertyName, (Property,), {
                "ontology": ontology,
                "domain": [Domain],
                "range": [Range]
            })

    # Rule 9: Individuals
    for collection in collections:
        result = db[collection].find()
        name = createdClasses.get(collection)
        i = 1
        subClasses = set()

        for instance in result:
            inst = name(f"{collection}_{i}", ontology=ontology)
            for key in instance.keys():
                if key != '_id':
                    val = instance.get(key)
                    if isinstance(val, list) and (not val or isinstance(val[0], dict) is False):
                        joined = ','.join(val)
                        inst.__setattr__(key, [joined])
                    else:
                        inst.__setattr__(key, [val])
                    if isinstance(val, dict) or (isinstance(val, list) and val and isinstance(val[0], dict)):
                        subClasses.add(key)

            i += 1

        for subclass in subClasses:
            types.new_class(subclass, (name,), {"ontology": ontology})

    # Rule 6: Disjointness
    disjointClasses = []
    ThingDisjointClasses = []
    for clas in ontology.classes:
        if clas.is_a == [Thing]:
            if clas not in ThingDisjointClasses:
                ThingDisjointClasses.append(clas)
        else:
            if clas not in disjointClasses:
                disjointClasses.append(clas)

    for class1 in ThingDisjointClasses:
        for class2 in ThingDisjointClasses:
            if class1 != class2:
                AllDisjoint(class1, class2)

    for class1 in disjointClasses:
        for class2 in disjointClasses:
            if class1 != class2 and class1.is_a == class2.is_a:
                AllDisjoint(class1, class2)

    def build_class_hierarchy_from_owlready(createdClasses):
        hierarchy = {cls: [] for cls in createdClasses}
        for cls_name, cls_obj in createdClasses.items():
            for parent in getattr(cls_obj, 'is_a', []):
                pname = parent.name
                if pname != cls_name and pname in hierarchy:
                    hierarchy[pname].append(cls_name)
        return hierarchy

    def build_class_tree(class_dict, current="Thing"):
        return {
            "name": current,
            "children": [build_class_tree(class_dict, child) for child in class_dict.get(current, [])]
        }

    class_hierarchy = build_class_hierarchy_from_owlready(createdClasses)
    class_tree = build_class_tree(class_hierarchy)

    # ✅ Save OWL once after mapping to improve export speed
    owl_path = os.path.join(settings.BASE_DIR, "ontology.owl")
    owl_content = to_owl(ontology)
    with io.open(owl_path, 'w', encoding='utf-8') as f:
        f.write(owl_content)
    request.session['owl_file_path'] = owl_path

    # 🧪 Preview only first and last 100 lines
    owl_lines = owl_content.splitlines()
    separator_line = " " * 1 + "-" * 100
    preview_note = " " * 1 + "..................................... 🔍 PREVIEW TRUNCATED ....................................."
    owl_preview = owl_lines[:100] + [separator_line, preview_note, separator_line] + owl_lines[-100:]

    request.session['mapping'] = {
        "classes": list(createdClasses.keys()),
        "object_properties": object_properties_display,
        "datatype_properties": sorted(
            [(k, sorted(list(v))) for k, v in datatype_properties_dict.items()],
            key=lambda x: x[0].lower()
        ),
        "class_dict": class_hierarchy,
        "class_tree": class_tree,
        "owl_preview": owl_preview
    }


    return render(request, 'mapping.html', {
        'mapping': request.session['mapping'],
        'class_tree': class_tree
    })


# STEP 5: Preview generated Ontology
def graph(request):

    mapping = request.session.get('mapping', {})

    if not mapping:
        return render(request, 'graph.html', {'error': 'No ontology data found.'})

    class_dict = mapping.get("class_dict", {})
    object_properties = mapping.get("object_properties", [])

    dot = Digraph(comment="Ontology Graph", format='png')
    dot.attr('node', shape='ellipse', style='filled', color='lightgoldenrod1', fontname='Helvetica')
    dot.attr('edge', fontsize='10', fontname='Helvetica')  # smaller font for edges

    # Add nodes
    for cls in mapping.get("classes", []):
        dot.node(cls)

    # Class hierarchy (solid blue)
    for parent, children in class_dict.items():
        for child in children:
            dot.edge(parent, child, arrowhead='onormal', color='blue')

    # Object properties (dashed, colored)
    color_palette = ['#d62728', '#2ca02c', '#ff7f0e', '#1f77b4', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    color_map = {}

    color_index = 0
    for prop in object_properties:
        if 'To' in prop:
            source, target = prop.split('To')
            if source in mapping['classes'] and target in mapping['classes']:
                if prop not in color_map:
                    color_map[prop] = color_palette[color_index % len(color_palette)]
                    color_index += 1

                dot.edge(
                    source,
                    target,
                    label=prop,
                    style='dashed',
                    color=color_map[prop],
                    fontcolor=color_map[prop],
                    labelfloat='false',
                    dir='forward'
                )

    # Save the graph to static folder
    static_path = os.path.join(settings.BASE_DIR, 'static')
    os.makedirs(static_path, exist_ok=True)
    graph_filename = os.path.join(static_path, "ontology_graph")
    dot.render(graph_filename, format='png', cleanup=True)

    return render(request, 'graph.html', {
        'graph_url': f"{settings.STATIC_URL}ontology_graph.png"
    })


# STEP 6: Export OWL
def export_owl(request):
    owl_path = request.session.get('owl_file_path')
    mapping = request.session.get('mapping', {})

    if not owl_path or not os.path.exists(owl_path):
        return render(request, "owl_viewer.html", {
            "mapping": mapping,
            "owl_data": "⚠️ OWL file not found. Please re-run mapping."
        })

    with open(owl_path, "r", encoding="utf-8") as f:
        owl_data = f.read()

    return render(request, "owl_viewer.html", {
        "mapping": mapping,
        "owl_data": owl_data,
        "owl_file_url": "/ontology.owl"
    })
