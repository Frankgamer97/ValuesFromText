import io
from time import sleep
import pydotplus
import rdflib
from IPython.display import display, Image
from rdflib.tools.rdf2dot import rdf2dot

def visualize(g):
    stream = io.StringIO()
    rdf2dot(g, stream, opts = {display})
    dg = pydotplus.graph_from_dot_data(stream.getvalue())
    png = dg.create_png()
    display(Image(png))


url = './data/rdf/32905117.ttl'

g = rdflib.Graph()
result = g.parse(url, format='turtle')

visualize(g)
sleep(60)